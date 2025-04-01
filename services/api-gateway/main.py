import os
import requests
import grpc
from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv

from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity

from app import post_pb2, post_pb2_grpc

load_dotenv()

app = Flask(__name__)

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user:5000/user")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret_key")

POST_SERVICE_HOST = "post"  
POST_SERVICE_PORT = "6000"

# ------------------------------------------------------------------
# USER
# ------------------------------------------------------------------

@app.route('/user/<path:path>', methods=['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
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

    response_headers = response.headers

    if response_headers.get('msg', None) == "Login is successful":
        response_headers["post_token"] = create_access_token(identity=response_headers.get('user_id', None))
        response_headers.pop('user_id', None)

    return Response(response.content, response.status_code, response_headers.items())


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


@app.route('/post/<path:path>', methods=['POST','GET','PUT','DELETE','PATCH'])
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
