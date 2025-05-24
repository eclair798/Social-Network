import os
import requests
import grpc
import json
from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from . import post_pb2, post_pb2_grpc
from . import stat_pb2, stat_pb2_grpc

from .config import USER_SERVICE_URL, POST_SERVICE_HOST, POST_SERVICE_PORT, STAT_SERVICE_HOST, STAT_SERVICE_PORT

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
        

    return Response(json.dumps(response_content), response.status_code, response.headers.items())

def check_user():
    url = f'{USER_SERVICE_URL}/check_user'
    headers = dict(request.headers)
    headers.pop('Host', None)
    response = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        json=request.get_json(),
        params=request.args
    )
    if response.status_code == 200:
        return response.json().get('user_id')
    return ""

# ------------------------------------------------------------------
# POST
# ------------------------------------------------------------------


def get_post_stub():
    channel = grpc.insecure_channel(f"{POST_SERVICE_HOST}:{POST_SERVICE_PORT}")
    return post_pb2_grpc.PostServiceStub(channel)

# Вспомогательные функции для каждого метода

@bp.route('/post/create', methods=['POST'])
def create_post():
    """
    POST /post/create
    """
    user_id = check_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    

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


@bp.route('/posts', methods=['GET'])
def list_posts():
    """
    GET /posts
    """   
    # user_id = check_user()
    # if not user_id:
    #     return jsonify({"error": "Unauthorized"}), 401
    
    
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

@bp.route('/post/<post_id>', methods=['GET'])
def get_post(post_id):
    """
    GET /post/<post_id>
    """
    user_id = check_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    

    stub = get_post_stub()
    
    req = post_pb2.GetPostRequest(
        post_id=post_id,
        user_id=user_id
    )

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


@bp.route('/post/<post_id>', methods=['PUT'])
def update_post(post_id):
    """
    PUT /post/<post_id>
    """
    user_id = check_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
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


@bp.route('/post/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """
    DELETE /post/<post_id>
    """
    user_id = check_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401


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


@bp.route('/post/<post_id>/like', methods=['POST'])
def like_post(post_id):
    user_id = check_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    stub = get_post_stub()
    req = post_pb2.LikePostRequest(post_id=post_id, user_id=user_id)
    try:
        resp = stub.LikePost(req)
        if resp.success:
            return jsonify({"message": resp.message}), 200
        else:
            return jsonify({"error": resp.message}), 400
    except grpc.RpcError as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/post/<post_id>/comment', methods=['POST'])
def comment_post(post_id):
    user_id = check_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    content = data.get("content", "")
    parent_comment_id = data.get("parent_comment_id", "")

    stub = get_post_stub()
    req = post_pb2.CommentPostRequest(
        post_id=post_id,
        user_id=user_id,
        content=content,
        parent_comment_id=parent_comment_id
    )

    try:
        resp = stub.CommentPost(req)
        if not resp.comment_id:
            return jsonify({"error": "Unable to create comment"}), 500
        return jsonify({
            "comment_id": resp.comment_id,
            "post_id":    resp.post_id,
            "user_id":    resp.user_id,
            "content":    resp.content,
            "created_at": resp.created_at
        }), 201
    except grpc.RpcError as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/post/<post_id>/comments', methods=['GET'])
def list_comments(post_id):
    # user_id = check_user()
    # if not user_id:
    #     return jsonify({"error": "Unauthorized"}), 401
    
    page = request.args.get('page', '1')
    page_size = request.args.get('page_size', '10')

    stub = get_post_stub()
    req = post_pb2.ListCommentsRequest(
        post_id=post_id,
        page=int(page),
        page_size=int(page_size)
    )
    try:
        resp = stub.ListComments(req)
        comments = []
        for c in resp.comments:
            comments.append({
                "comment_id": c.comment_id,
                "post_id":    c.post_id,
                "user_id":    c.user_id,
                "content":    c.content,
                "created_at": c.created_at
            })
        return jsonify({"total": resp.total, "comments": comments}), 200
    except grpc.RpcError as e:
        return jsonify({"error": str(e)}), 500



@bp.route('/<path:path>', methods=['POST','GET','PUT','DELETE','PATCH'])
def proxy_post(path):
    user_id = check_user()
    if not user_id:
       return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"error": "Not implemented or invalid route"}), 404


# ------------------------------------------------------------------
# STAT
# ------------------------------------------------------------------

def get_stat_stub():
    channel = grpc.insecure_channel(f"{STAT_SERVICE_HOST}:{STAT_SERVICE_PORT}")
    return stat_pb2_grpc.StatServiceStub(channel)

@bp.route('/stat/post/<post_id>', methods=['GET'])
def post_stats(post_id):
    stub = get_stat_stub()
    req = stat_pb2.PostIdRequest(post_id=post_id)
    resp = stub.GetPostStats(req)
    return jsonify({
        "views": resp.views,
        "likes": resp.likes,
        "comments": resp.comments
    })

@bp.route('/stat/post/<post_id>/views_by_day', methods=['GET'])
def post_views_by_day(post_id):
    stub = get_stat_stub()
    req = stat_pb2.PostIdRequest(post_id=post_id)
    resp = stub.GetPostViewsByDay(req)
    return jsonify([{ "date": d.date, "count": d.count } for d in resp.by_day])

@bp.route('/stat/post/<post_id>/likes_by_day', methods=['GET'])
def post_likes_by_day(post_id):
    stub = get_stat_stub()
    req = stat_pb2.PostIdRequest(post_id=post_id)
    resp = stub.GetPostLikesByDay(req)
    return jsonify([{ "date": d.date, "count": d.count } for d in resp.by_day])

@bp.route('/stat/post/<post_id>/comments_by_day', methods=['GET'])
def post_comments_by_day(post_id):
    stub = get_stat_stub()
    req = stat_pb2.PostIdRequest(post_id=post_id)
    resp = stub.GetPostCommentsByDay(req)
    return jsonify([{ "date": d.date, "count": d.count } for d in resp.by_day])

@bp.route('/stat/top_posts', methods=['GET'])
def top_posts():
    metric = request.args.get('metric', 'like')
    stub = get_stat_stub()
    req = stat_pb2.TopRequest(metric=metric)
    resp = stub.GetTopPosts(req)
    return jsonify([{ "post_id": item.id, "count": item.value } for item in resp.top_items])

@bp.route('/stat/top_users', methods=['GET'])
def top_users():
    metric = request.args.get('metric', 'like')
    stub = get_stat_stub()
    req = stat_pb2.TopRequest(metric=metric)
    resp = stub.GetTopUsers(req)
    return jsonify([{ "user_id": item.id, "count": item.value } for item in resp.top_items])

