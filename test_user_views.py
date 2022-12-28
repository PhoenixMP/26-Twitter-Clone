"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        # Building database of users
        self.mainuser = User(username="mainuser",
                             email="test@test.com", password="testing")
        self.user1 = User(username="testuser1",
                          email="1test@test.com", password="testing")
        self.user2 = User(username="testuser2",
                          email="2test@test.com", password="testing")
        self.user3 = User(username="testuser3",
                          email="3test@test.com", password="testing")
        self.user4 = User(username="testuser4",
                          email="4test@test.com", password="testing")

        db.session.add_all(
            [self.mainuser, self.user1, self.user2, self.user3, self.user4])
        db.session.commit()

        self.mainuser_id = 1000
        self.mainuser.id = self.mainuser_id
        self.user1_id = 1001
        self.user1.id = self.user1_id
        self.user2_id = 1002
        self.user2.id = self.user2_id
        self.user3_id = 1003
        self.user3.id = self.user3_id
        self.user4_id = 1004
        self.user4.id = self.user4_id
        db.session.commit()

        self.msg0 = Message(
            text=f'I am the main user', user_id=self.mainuser.id)
        self.msg1 = Message(
            text=f'I am user number 1', user_id=self.user1.id)
        self.msg2 = Message(
            text=f'I am user number 2', user_id=self.user2.id)
        self.msg3 = Message(
            text=f'I am user number 3', user_id=self.user3.id)
        self.msg4 = Message(
            text=f'I am user number 4', user_id=self.user4.id)

        db.session.add_all(
            [self.msg0, self.msg1, self.msg2, self.msg3, self.msg4])
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_list_users(self):
        """Do all 4 usesr show up when logged in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser.id

            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # Test that all of the 4 user cards show up, not including the logged in user
            self.assertIn("testuser1", html)
            self.assertIn("testuser2", html)
            self.assertIn("testuser3", html)
            self.assertIn("testuser4", html)

    def test_search_users(self):
        """Does only searched user show up"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser.id

            # Only searched user appears after a query search
            resp = c.get("/users?q=testuser1")
            html = resp.get_data(as_text=True)
            self.assertIn("testuser1", html)
            self.assertNotIn("testuser2", html)
            self.assertNotIn("testuser3", html)
            self.assertNotIn("testuser4", html)

    def test_show_user(self):
        """Does one user appear, including the logged in user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser.id

            resp = c.get(f"/users/{self.user1_id}")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)

            # the user and their message should be in html
            self.assertIn("testuser1", html)
            self.assertIn("I am user number 1", html)

            resp = c.get(f"/users/{self.mainuser_id}")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)

            # the logged in user and their message should be in html
            self.assertIn("mainuser", html)
            self.assertIn("I am the main user", html)

    def test_show_following(self):
        """Do you see a list of who a user follows"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser.id
            main = User.query.get_or_404(
                self.mainuser_id)
            followed_user1 = User.query.get_or_404(self.user1_id)
            followed_user2 = User.query.get_or_404(self.user2_id)

            main.following.append(followed_user1)
            main.following.append(followed_user2)
            followed_user1.following.append(main)

            db.session.commit()

            resp = c.get(f"/users/{self.mainuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)

            # mainuser should be following testuser1 and testuser2 only
            self.assertIn("testuser1", html)
            self.assertIn("testuser2", html)
            self.assertNotIn("testuser3", html)

            resp = c.get(f"/users/{self.user1_id}/following")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)

            # user1 should be following main only
            self.assertIn("mainuser", html)
            self.assertNotIn("testuser2", html)
            self.assertNotIn("testuser3", html)

    def test_users_followers(self):
        """Do you see a list of who is following a user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser.id
            main = User.query.get_or_404(
                self.mainuser_id)
            user1 = User.query.get_or_404(self.user1_id)
            user2 = User.query.get_or_404(self.user2_id)

            main.followers.append(user1)
            main.followers.append(user2)
            user1.followers.append(main)

            db.session.commit()

            resp = c.get(f"/users/{self.mainuser_id}/followers")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)

            # mainuser should have testuser1 and testuser2 as followers
            self.assertIn("testuser1", html)
            self.assertIn("testuser2", html)
            self.assertNotIn("testuser3", html)

            resp = c.get(f"/users/{self.user1_id}/following")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)

            # user1 should have main be the only follower
            self.assertIn("mainuser", html)
            self.assertNotIn("testuser2", html)
            self.assertNotIn("testuser3", html)

    def test_add_follow(self):
        """Can logged in user follow another user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser.id

            resp = c.post(f"/users/follow/{self.user1_id}")

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            # main user should be following just one user, user1.
            main = User.query.get_or_404(self.mainuser_id)
            self.assertEqual(len(main.following), 1)
            self.assertEqual(main.following[0],
                             User.query.get_or_404(self.user1_id))

    def test_stop_following(self):
        """Can logged in user stop following another user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser.id

            main = User.query.get_or_404(
                self.mainuser_id)
            user1 = User.query.get_or_404(self.user1_id)
            main.following.append(user1)
            db.session.commit()

            resp = c.post(f"/users/stop-following/{self.user1_id}")

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            # main user should be following no users
            main = User.query.get_or_404(self.mainuser_id)
            self.assertEqual(len(main.following), 0)

    def test_add_like(self):
        """Test that user can like a message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser_id
            m = Message(user_id=self.user1_id, text="hello")
            m_id = 1000
            m.id = m_id
            db.session.add(m)
            db.session.commit()

            resp = c.post(
                f"/messages/{m_id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(
                Likes.user_id == self.mainuser_id).all()

            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].message_id, m_id)

            # The second time "posting" this like route, like should be removed
            resp = c.post(
                f"/messages/{m_id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(
                Likes.user_id == self.mainuser_id).all()

            self.assertEqual(len(likes), 0)

    def test_like_show(self):
        """Test that user can veiw all liked messages"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.mainuser_id
            m1 = Message(user_id=self.user1_id, text="hello")
            m2 = Message(user_id=self.user2_id, text="huzzah")
            m1_id = 1000
            m1.id = m1_id
            m2_id = 1001
            m2.id = m2_id
            db.session.add_all([m1, m2])
            db.session.commit()

            c.post(
                f"/messages/{m1_id}/like", follow_redirects=True)
            c.post(
                f"/messages/{m2_id}/like", follow_redirects=True)

            resp = c.get(
                f"/users/{self.mainuser_id}/likes")
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(
                Likes.user_id == self.mainuser_id).all()
            html = resp.get_data(as_text=True)
            self.assertIn("hello", html)
            self.assertIn("huzzah", html)
