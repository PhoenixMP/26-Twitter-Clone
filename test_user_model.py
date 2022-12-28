"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
    """Test attributes of user."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(f'{u}', f'<User #{u.id}: testuser, test@test.com>')

    def test_user2_is_following_user1(self):
        """Does is_following and is_followed_by work? (user2 follows user1)"""

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )
        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([user1, user2])
        db.session.commit()

        f = Follows(user_being_followed_id=user1.id,
                    user_following_id=user2.id)
        db.session.add(f)
        db.session.commit()

        self.assertEqual(user1.is_following(user2), False)
        self.assertEqual(user2.is_following(user1), True)
        self.assertEqual(user1.is_followed_by(user2), True)
        self.assertEqual(user2.is_followed_by(user1), False)

    def test_user1_is_following_user2(self):
        """Does is_following and is_followed_by work? (user1 follows user2)"""

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )
        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([user1, user2])
        db.session.commit()

        f = Follows(user_being_followed_id=user2.id,
                    user_following_id=user1.id)
        db.session.add(f)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(user1.is_following(user2), True)
        self.assertEqual(user2.is_following(user1), False)
        self.assertEqual(user1.is_followed_by(user2), False)
        self.assertEqual(user2.is_followed_by(user1), True)

    def test_user_requirements(self):
        """Are there requirements on creating a new user?"""

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )
        # user2 has repeat email of user 1
        user2 = User(
            email="test1@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )
        # user3 has repeat username of user 1
        user3 = User(
            email="test3@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )
        # user4 has no username
        user4 = User(
            email="test4@test.com",
            username="",
            password="HASHED_PASSWORD"
        )
        # user5 has no email
        user5 = User(
            email="",
            username="testuser5",
            password="HASHED_PASSWORD"
        )
        # user6 has no password
        user6 = User(
            email="testuser6@test.com",
            username="testuser6",
            password=""
        )

        db.session.add(user1)
        db.session.commit()
        errors = 0

        try:
            db.session.add(user2)
            db.session.commit()
        except:
            errors += 1
        try:
            db.session.add(user3)
            db.session.commit()
        except:
            errors += 1
        try:
            db.session.add(user4)
            db.session.commit()
        except:
            errors += 1
        try:
            db.session.add(user5)
            db.session.commit()
        except:
            errors += 1
        try:
            db.session.add(user6)
            db.session.commit()
        except:
            errors += 1

        # user1 should be the only user that was made, the other 5 should create erros
        self.assertEqual(errors, 5)

    def test_authenticate(self):
        """Does User.authenticate on return a user with valid login?"""

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD",
            image_url="http://t0.gstatic.com/licensed-image?q=tbn:ANd9GcQnDrlslZGI5Wa-6GgzdxVCgKbi6NTgJHagHTfuoNs_d7fl8mg5gDqYrvPYt6RNm364BQZps6KpleNpd_k"
        )

        user = User.signup(
            user1.username, user1.email, user1.password, user1.image_url)

        # User should have no messages & no followers
        self.assertEqual(User.authenticate(
            "testuser1", "HASHED_PASSWORD"), user)
        self.assertEqual(User.authenticate(
            "WRONG_USER", user.password), False)
        self.assertEqual(User.authenticate(
            "testuser1", "WRONG_PASSWORD"), False)
        self.assertEqual(User.authenticate("", "WRONG_PASSWORD"), False)
        self.assertEqual(User.authenticate("testuser1", ""), False)
