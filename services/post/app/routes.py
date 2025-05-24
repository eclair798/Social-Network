import uuid
import time
from concurrent import futures
import grpc
from sqlalchemy.exc import SQLAlchemyError
from .database import db
from .models import Post, Comment, Like
from datetime import datetime

from app import post_pb2, post_pb2_grpc
from .kafka_producer import produce_event


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
            
            if request.user_id:
                # отправляем событие
                produce_event(
                    topic="action-views",
                    user_id=request.user_id,
                    entity_id=request.post_id,
                    action_type="view"
                )

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

    def LikePost(self, request, context):
        with self.app.app_context():
            post = Post.query.filter_by(post_id=request.post_id, is_deleted=False).first()
            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or deleted")
                return post_pb2.LikePostResponse(success=False, message="No post")
            
            existing_like = Like.query.filter_by(post_id=request.post_id, user_id=request.user_id).first()
            if existing_like:
                return post_pb2.LikePostResponse(success=True, message="Already liked")

            new_like = Like(
                post_id=request.post_id,
                user_id=request.user_id
            )
            try:
                db.session.add(new_like)
                db.session.commit()
                # отправляем событие
                produce_event(
                    topic="action-likes",
                    user_id=request.user_id,
                    entity_id=request.post_id,
                    action_type="like"
                )
                return post_pb2.LikePostResponse(success=True, message="Liked successfully")
            except SQLAlchemyError as e:
                db.session.rollback()
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(e))
                return post_pb2.LikePostResponse(success=False, message="Failed")

    def CommentPost(self, request, context):
        with self.app.app_context():
            post = Post.query.filter_by(post_id=request.post_id, is_deleted=False).first()
            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Post not found or deleted")
                return post_pb2.CommentPostResponse()

            new_comment = Comment(
                post_id=request.post_id,
                user_id=request.user_id,
                content=request.content,
                parent_comment_id=request.parent_comment_id if request.parent_comment_id else None
            )
            try:
                db.session.add(new_comment)
                db.session.commit()
                # отправляем событие
                produce_event(
                    topic="action-comments",
                    user_id=request.user_id,
                    entity_id=request.post_id,
                    action_type="comment"
                )
                return post_pb2.CommentPostResponse(
                    comment_id=new_comment.comment_id,
                    post_id=new_comment.post_id,
                    user_id=new_comment.user_id,
                    content=new_comment.content,
                    created_at=str(new_comment.created_at)
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(e))
                return post_pb2.CommentPostResponse()

    def ListComments(self, request, context):
        with self.app.app_context():
            page = request.page or 1
            page_size = request.page_size or 10

            query = Comment.query.filter_by(post_id=request.post_id)
            total = query.count()
            comments = query.order_by(Comment.created_at.desc()) \
                            .limit(page_size) \
                            .offset((page - 1)*page_size) \
                            .all()
            
            resp = post_pb2.ListCommentsResponse(total=total)
            for c in comments:
                comment_data = post_pb2.CommentData(
                    comment_id=c.comment_id,
                    post_id=c.post_id,
                    user_id=c.user_id,
                    content=c.content,
                    created_at=str(c.created_at)
                )
                resp.comments.append(comment_data)
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
