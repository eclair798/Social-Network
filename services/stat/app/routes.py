import time
from concurrent import futures

import grpc

from app import stat_pb2, stat_pb2_grpc
from .clickhouse import get_client

class StatServiceServicer(stat_pb2_grpc.StatServiceServicer):
    def __init__(self):
        self.ch = get_client()

    def GetPostStats(self, request, context):
        post_id = request.post_id
        q = '''
        SELECT
          sum(action_type='view') as views,
          sum(action_type='like') as likes,
          sum(action_type='comment') as comments
        FROM actions
        WHERE entity_id=%(post_id)s
        '''
        result = self.ch.execute(q, {'post_id': post_id})[0]
        return stat_pb2.PostStatsResponse(
            views = result[0] or 0,
            likes = result[1] or 0,
            comments = result[2] or 0
        )

    def GetPostViewsByDay(self, request, context):
        post_id = request.post_id
        q = '''
        SELECT toDate(timestamp) as dt, count(*)
        FROM actions
        WHERE entity_id=%(post_id)s AND action_type='view'
        GROUP BY dt
        ORDER BY dt
        '''
        res = self.ch.execute(q, {'post_id': post_id})
        resp = stat_pb2.StatsByDayResponse()
        for row in res:
            resp.by_day.add(date=str(row[0]), count=row[1])
        return resp

    def GetPostLikesByDay(self, request, context):
        post_id = request.post_id
        q = '''
        SELECT toDate(timestamp) as dt, count(*)
        FROM actions
        WHERE entity_id=%(post_id)s AND action_type='like'
        GROUP BY dt
        ORDER BY dt
        '''
        res = self.ch.execute(q, {'post_id': post_id})
        resp = stat_pb2.StatsByDayResponse()
        for row in res:
            resp.by_day.add(date=str(row[0]), count=row[1])
        return resp

    def GetPostCommentsByDay(self, request, context):
        post_id = request.post_id
        q = '''
        SELECT toDate(timestamp) as dt, count(*)
        FROM actions
        WHERE entity_id=%(post_id)s AND action_type='comment'
        GROUP BY dt
        ORDER BY dt
        '''
        res = self.ch.execute(q, {'post_id': post_id})
        resp = stat_pb2.StatsByDayResponse()
        for row in res:
            resp.by_day.add(date=str(row[0]), count=row[1])
        return resp

    def GetTopPosts(self, request, context):
        metric = request.metric
        # metric = view, like, comment
        q = f'''
        SELECT entity_id, count(*) as cnt
        FROM actions
        WHERE action_type=%(metric)s
        GROUP BY entity_id
        ORDER BY cnt DESC
        LIMIT 10
        '''
        res = self.ch.execute(q, {'metric': metric})
        resp = stat_pb2.TopResponse()
        for row in res:
            resp.top_items.add(id=row[0], value=row[1])
        return resp

    def GetTopUsers(self, request, context):
        metric = request.metric
        q = f'''
        SELECT user_id, count(*) as cnt
        FROM actions
        WHERE action_type=%(metric)s
        GROUP BY user_id
        ORDER BY cnt DESC
        LIMIT 10
        '''
        res = self.ch.execute(q, {'metric': metric})
        resp = stat_pb2.TopResponse()
        for row in res:
            resp.top_items.add(id=row[0], value=row[1])
        return resp

def serve_grpc_server(port=7000):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    stat_pb2_grpc.add_StatServiceServicer_to_server(StatServiceServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Stat [gRPC] server running on {port}")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
