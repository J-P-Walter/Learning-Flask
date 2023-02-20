import os
os.environ['DATABASE_URL'] = 'sqlite://' #use own database without touching the already created one
from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Post

#Unit tests for testing User model
class UserModelCase(unittest.TestCase):
    #Setup test, used by unittest library
    def setUp(self):
        self.app_context = app.app_context()   
        self.app_context.push()
        db.create_all()

    #Teardown test, used by unittest library
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    #Testing password hashing
    def test_password_hashing(self):
        u = User(username='test')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    #Testing following
    def test_follow(self):
        u1 = User(username='user1', email='user1@example.com')
        u2 = User(username='user2', email='user2@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u2.followed.all(), [])

        #Tests for both followed and followers
        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'user2')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'user1')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(),0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        u1 = User(username='user1', email='user1@example.com')
        u2 = User(username='user2', email='user2@example.com')
        u3 = User(username='user3', email='user3@example.com')
        u4 = User(username='user4', email='user4@example.com')
        db.session.add_all([u1, u2, u3, u4])

        now = datetime.utcnow()
        p1 = Post(body='post from user1', author=u1, timestamp=now+timedelta(seconds=1))
        p2 = Post(body='post from user2', author=u2, timestamp=now+timedelta(seconds=4))
        p3 = Post(body='post from user3', author=u3, timestamp=now+timedelta(seconds=3))
        p4 = Post(body='post from user4', author=u4, timestamp=now+timedelta(seconds=2))    
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)
        u1.follow(u4) 
        u2.follow(u3)  
        u3.follow(u4)  
        db.session.commit()

        #Check posts, should be u1 sees 3, u2 sees 2, u3 sees 2, and u4 sees 1
        #Own posts show up as well
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])

if __name__ == '__main__':
    unittest.main(verbosity=2)
