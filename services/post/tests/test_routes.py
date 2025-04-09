import pytest
import grpc
from concurrent import futures

from app import create_app, create_db_with_retries, db
from app.models import Post
from app.routes import PostServiceServicer
from app.post_pb2_grpc import add_PostServiceServicer_to_server, PostServiceStub
from app.post_pb2 import CreatePostRequest, GetPostRequest, DeletePostRequest, UpdatePostRequest, ListPostsRequest

@pytest.fixture(scope="module")
def test_app():
    app = create_app(testing=True)
    create_db_with_retries(app, db, retries=1, delay=0)
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture(scope="module")
def grpc_server(test_app):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    add_PostServiceServicer_to_server(PostServiceServicer(test_app), server)
    port = server.add_insecure_port('localhost:0')
    server.start()

    yield server, port

    server.stop(None)

@pytest.fixture
def grpc_stub(grpc_server):
    server, port = grpc_server
    channel = grpc.insecure_channel(f'localhost:{port}')
    stub = PostServiceStub(channel)
    return stub

def test_create_post_success(test_app, grpc_stub):
    req = CreatePostRequest(
        user_id="some_user_id",
        content="Test content"
    )
    resp = grpc_stub.CreatePost(req)
    assert resp.post_id is not None
    assert resp.content == "Test content"
    assert resp.is_deleted is False

    with test_app.app_context():
        post_obj = Post.query.filter_by(post_id=resp.post_id).first()
        assert post_obj is not None
        assert post_obj.content == "Test content"

def test_get_post_success(test_app, grpc_stub):
    with test_app.app_context():
        from app.models import Post
        new_post = Post(user_id="user42", content="Hello!")
        db.session.add(new_post)
        db.session.commit()
        saved_id = new_post.post_id

    req = GetPostRequest(post_id=saved_id)
    resp = grpc_stub.GetPost(req)
    assert resp.post_id == saved_id
    assert resp.content == "Hello!"
    assert resp.user_id == "user42"

def test_delete_post_denied(test_app, grpc_stub):
    with test_app.app_context():
        post_db = Post(user_id="creator", content="Will delete me")
        db.session.add(post_db)
        db.session.commit()
        post_id = post_db.post_id

    req = DeletePostRequest(post_id=post_id, user_id="someone_else")
    del_resp = grpc_stub.DeletePost(req)
    assert del_resp.success is False
    assert "Permission Denied" in del_resp.message

    req_ok = DeletePostRequest(post_id=post_id, user_id="creator")
    del_resp_ok = grpc_stub.DeletePost(req_ok)
    assert del_resp_ok.success is True
