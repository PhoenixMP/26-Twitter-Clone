"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

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


class MessageModelTestCase(TestCase):
    """Test attributes of message model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        msg = Message(
            text="test message",
            user_id=u.id
        )

        db.session.add(msg)
        db.session.commit()

        # User should have one message
        self.assertEqual(len(u.messages), 1)
        self.assertEqual(u.messages[0].text, "test message")

    def test_message_requirements(self):
        """Are there requirements on creating a new message?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        msg1 = Message(
            text="test message",
            user_id=u.id
        )
        msg2 = Message(
            text=None,
            user_id=u.id
        )
        msg3 = Message(
            text="test message",
        )
        long_string = 'jsflaksjdfklajsdlfkjasljfiowejfoiaewjfiojwaeoifjjsflaksjdfklajsdlfkjasljfiowejfoiaewjfiojwaeoifjjsflaksjdfklajsdlfkjasljfiowejfoiaewjfiojwaeoifjjsflaksjdfklajsdlfkjasljfiowejfoiaewjfiojwaeoifj'
        msg4 = Message(
            text=long_string,
            user_id=u.id
        )

        errors = []
        try:
            db.session.add(msg1)
            db.session.commit()
        except:
            errors += ["msg1"]
        try:
            db.session.add(msg2)
            db.session.commit()
        except:
            errors += ["msg2"]
        try:
            db.session.add(msg3)
            db.session.commit()
        except:
            errors += ["msg3"]
        try:
            db.session.add(msg4)
            db.session.commit()
        except:
            errors += ["msg4"]

        # Only the first message should be accepted, three errors
        self.assertEqual(errors, ["msg2", "msg3", "msg4"])

    def test_message_likes(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        msg = Message(
            text="test message",
            user_id=u.id
        )

        db.session.add(msg)
        db.session.commit()

        like1 = Likes(
            user_id=u.id,
            message_id=msg.id
        )

        like2 = Likes(
            user_id=u.id,
            message_id=msg.id
        )
        errors = 0

        db.session.add(like1)
        db.session.commit()

        try:
            db.session.add(like2)
            db.session.commit()
        except:
            errors += 1

        # a message can only have one like per user.
        self.assertEqual(errors, 1)
