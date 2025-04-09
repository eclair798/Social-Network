import os
import requests
import grpc
import json
from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from . import post_pb2, post_pb2_grpc

from .config import USER_SERVICE_URL, POST_SERVICE_HOST, POST_SERVICE_PORT

bp = Blueprint('routes', __name__)

# ------------------------------------------------------------------
# USER
# ------------------------------------------------------------------

@bp.route('/user/<path:path>', methods=['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    url = f'{USER_SERVICE_URL}/{path}'
    
    headers = dict(request.headers)
    headers.pop('Host', None)

    response = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        json=request.get_json(),
        params=request.args
    )

    try:
        response_content = response.json()
    except ValueError:
        response_content = {}

    if response_content.get("msg") == "Login is successful":
        response_content["post_token"] = create_access_token(identity=response_content.get("user_id"))
        response_content.pop("user_id", None)

    return Response(json.dumps(response_content), response.status_code, response.headers.items())


# ------------------------------------------------------------------
# POST
# ------------------------------------------------------------------

def get_post_stub():
    channel = grpc.insecure_channel(f"{POST_SERVICE_HOST}:{POST_SERVICE_PORT}")
    return post_pb2_grpc.PostServiceStub(channel)

# Вспомогательные функции для каждого метода

def handle_create_post(user_id):
    """
    POST /post/create
    """
    data = request.get_json() or {}
    content = data.get("content", "")
    stub = get_post_stub()

    req = post_pb2.CreatePostRequest(
        user_id=user_id,
        content=content
    )
    try:
        resp = stub.CreatePost(req)
        if not resp.post_id:
            return jsonify({"error": "Failed to create post"}), 500

        return jsonify({
            "post_id":   resp.post_id,
            "user_id":   resp.user_id,
            "content":   resp.content,
            "created_at":resp.created_at,
            "updated_at":resp.updated_at,
            "is_deleted":resp.is_deleted
        }), 201
    except grpc.RpcError as e:
        return jsonify({"error": str(e)}), 500


def handle_list_posts():
    """
    GET /post/list
    """
    page = request.args.get('page', '1')
    page_size = request.args.get('page_size', '10')
    stub = get_post_stub()

    req = post_pb2.ListPostsRequest(
        page=int(page),
        page_size=int(page_size)
    )

    try:
        resp = stub.ListPosts(req)
        posts_data = []
        for p in resp.posts:
            posts_data.append({
                "post_id":    p.post_id,
                "user_id":    p.user_id,
                "content":    p.content,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "is_deleted": p.is_deleted
            })
        return jsonify({"total": resp.total, "posts": posts_data}), 200
    except grpc.RpcError as e:
        return jsonify({"error": str(e)}), 500


def handle_get_post(post_id):
    """
    GET /post/<post_id>
    """
    stub = get_post_stub()
    req = post_pb2.GetPostRequest(post_id=post_id)
    try:
        resp = stub.GetPost(req)
        if not resp.post_id:
            return jsonify({"error": "Post not found"}), 404
        return jsonify({
            "post_id":    resp.post_id,
            "user_id":    resp.user_id,
            "content":    resp.content,
            "created_at": resp.created_at,
            "updated_at": resp.updated_at,
            "is_deleted": resp.is_deleted
        }), 200
    except grpc.RpcError as e:
        return jsonify({"error": str(e)}), 500


def handle_update_post(post_id, user_id):
    """
    PUT /post/<post_id>
    """
    data = request.get_json() or {}
    content = data.get("content", "")
    stub = get_post_stub()

    req = post_pb2.UpdatePostRequest(
        post_id=post_id,
        user_id=user_id,
        content=content
    )

    try:
        resp = stub.UpdatePost(req)
        if not resp.post_id:
            return jsonify({"error": "Not found or no permission"}), 404
        return jsonify({
            "post_id":    resp.post_id,
            "user_id":    resp.user_id,
            "content":    resp.content,
            "created_at": resp.created_at,
            "updated_at": resp.updated_at,
            "is_deleted": resp.is_deleted
        }), 200
    except grpc.RpcError as e:
        return jsonify({"error": str(e)}), 500


def handle_delete_post(post_id, user_id):
    """
    DELETE /post/<post_id>
    """
    stub = get_post_stub()
    req = post_pb2.DeletePostRequest(
        post_id=post_id,
        user_id=user_id
    )
    try:
        resp = stub.DeletePost(req)
        if not resp.success:
            return jsonify({"error": resp.message}), 403
        return jsonify({"msg": "Post deleted"}), 200
    except grpc.RpcError as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/post/<path:path>', methods=['POST','GET','PUT','DELETE','PATCH'])
@jwt_required()
def proxy_post(path):

    user_id = get_jwt_identity()

    if request.method == 'POST':
        if path == 'create':
            return handle_create_post(user_id)
        else:
            return jsonify({"error": "Unsupported POST endpoint"}), 404

    elif request.method == 'GET':
        if path == 'list':
            return handle_list_posts()
        else:
            return handle_get_post(path)

    elif request.method == 'PUT':
        return handle_update_post(path, user_id)

    elif request.method == 'DELETE':
        return handle_delete_post(path, user_id)

    return jsonify({"error": "Not implemented or invalid route"}), 404

