"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_show_message(self):
        """Can user see a single message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            msg = Message(text="test message",
                          user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.get(f'messages/{msg.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('test message', html)

    def test_destroy_message(self):
        """Can user delete a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message(text="test message",
                          user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.post(f'messages/{msg.id}/delete')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(Message.query.all()), 0)

###############################################################
# Testing Messages without authentication

    def test_unathenticated_add_message(self):
        """Can someone add a message if not logged in?"""

        with self.client as c:
            resp = c.post("/messages/new",
                          data={"text": "Hello"}, follow_redirects=True)

            # Make sure it does not redirects
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            # No messages should have been added
            self.assertEqual(Message.query.all(), [])

    def test_unathenticated_show_message(self):
        """Can someone see a single message if not logged in?"""

        with self.client as c:

            msg = Message(text="test message",
                          user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.get(f'messages/{msg.id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unathenticated_destroy_message(self):
        """Can someone delete a message if not logged in?"""

        with self.client as c:

            msg = Message(text="test message",
                          user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.post(f'messages/{msg.id}/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


###############################################################
# Testing Messages without authorization

    def test_unathorized_add_message(self):
        """Can unauthorized user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Create the user that will be have message made for them
            user1 = User(username="test1",
                         email="test1@test.com",
                         password="testuser",
                         image_url=None)

            db.session.add(user1)
            db.session.commit()

            # Try to make a message with another user ID
            resp = c.post(
                "/messages/new", data={"text": "Hello", "user_id": user1.id})
            self.assertEqual(resp.status_code == 302, True)

            msg = Message.query.one()

            # The message made is only added to the current user in session.
            self.assertEqual(msg.user_id, self.testuser.id)

    def test_unathorized_destroy_message(self):
        """Can unauthorized user delete a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

             # Create the user that will make a message that will be deleted by session user
            user1 = User(username="test1",
                         email="test1@test.com",
                         password="testuser",
                         image_url=None)

            db.session.add(user1)
            db.session.commit()

            msg = Message(text="test message",
                          user_id=user1.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.post(f'messages/{msg.id}/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
