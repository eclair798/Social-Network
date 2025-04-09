import uuid
import time
from concurrent import futures
import grpc
from sqlalchemy.exc import SQLAlchemyError
from .database import db
from .models import Post
from datetime import datetime


from app import post_pb2, post_pb2_grpc


class PostServiceServicer(post_pb2_grpc.PostServiceServicer):

    def __init__(self, flask_app):
        self.app = flask_app

    def CreatePost(self, request, context):
        with self.app.app_context():
            try:
                new_post = Post(
                    user_id=request.user_id,
                    content=request.content
                )
                db.session.add(new_post)
                db.session.commit()
                return post_pb2.PostResponse(
                    post_id=new_post.post_id,
                    user_id=new_post.user_id,
                    content=new_post.content,
                    created_at=str(new_post.created_at),
                    updated_at=str(new_post.updated_at),
                    is_deleted=new_post.is_deleted
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(e))
                return post_pb2.PostResponse()

    def GetPost(self, request, context):
        with self.app.app_context():
            post = Post.query.filter_by(post_id=request.post_id, is_deleted=False).first()
            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or is deleted")
                return post_pb2.PostResponse()
            return post_pb2.PostResponse(
                post_id=post.post_id,
                user_id=post.user_id,
                content=post.content,
                created_at=str(post.created_at),
                updated_at=str(post.updated_at),
                is_deleted=post.is_deleted
            )

    def UpdatePost(self, request, context):
        with self.app.app_context():
            post = Post.query.filter_by(post_id=request.post_id, is_deleted=False).first()
            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or deleted")
                return post_pb2.PostResponse()
            if post.user_id != request.user_id:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("You are not the owner of this post")
                return post_pb2.PostResponse()

            try:
                post.content = request.content
                post.updated_at = datetime.utcnow()
                db.session.commit()
                return post_pb2.PostResponse(
                    post_id=post.post_id, user_id=post.user_id,
                    content=post.content,
                    created_at=str(post.created_at),
                    updated_at=str(post.updated_at),
                    is_deleted=post.is_deleted
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(e))
                return post_pb2.PostResponse()

    def DeletePost(self, request, context):
        with self.app.app_context():
            post = Post.query.filter_by(post_id=request.post_id, is_deleted=False).first()
            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or already deleted")
                return post_pb2.DeletePostResponse(success=False, message="Not found")

            if post.user_id != request.user_id:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("You are not the owner of this post")
                return post_pb2.DeletePostResponse(success=False, message="Permission Denied")

            post.is_deleted = True
            db.session.commit()
            return post_pb2.DeletePostResponse(success=True, message="Post deleted")

    def ListPosts(self, request, context):
        with self.app.app_context():
            page = request.page or 1
            page_size = request.page_size or 10
            query = Post.query.filter_by(is_deleted=False)

            total = query.count()
            posts = query.order_by(Post.created_at.desc()) \
                         .limit(page_size) \
                         .offset((page-1)*page_size) \
                         .all()

            resp = post_pb2.ListPostsResponse(total=total)
            for p in posts:
                post_resp = post_pb2.PostResponse(
                    post_id=p.post_id,
                    user_id=p.user_id,
                    content=p.content,
                    created_at=str(p.created_at),
                    updated_at=str(p.updated_at),
                    is_deleted=p.is_deleted
                )
                resp.posts.append(post_resp)
            return resp


def serve_grpc_server(flask_app, port=6000):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    post_pb2_grpc.add_PostServiceServicer_to_server(PostServiceServicer(flask_app), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Post gRPC server is running on port {port}")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
