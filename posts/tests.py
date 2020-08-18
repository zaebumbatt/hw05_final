import time

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import User, Post, Group


class TestPosts(TestCase):
    def setUp(self):
        self.login_client = Client()
        self.logout_client = Client()
        self.user = User.objects.create_user(username='test', password='testpassword12345', email='test@yandex.ru')
        self.login_client.force_login(self.user)
        self.logout_client.logout()
        self.posts_count = Post.objects.count()
        self.group = Group.objects.create(title='testgroup', slug='testslug')
        self.post = Post.objects.create(text='Test post', author=self.user, group=self.group)

    def test_new_post(self):
        new_post_data = {'text': 'Test post again', 'author': self.user.username, 'group': self.group.id}
        response = self.login_client.post(reverse('new_post'), new_post_data, follow=True)
        self.assertEqual(response.status_code, 200)  # Check if new user can create a post

        time.sleep(20)  # 20 seconds wait because index page is cached

        response_index = self.login_client.get(reverse('index'))
        self.assertContains(response_index, 'Test post again')  # Check if new post added to /index/ page

        response_profile = self.login_client.get(reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(response_profile, 'Test post again')  # Check if new post added to /profile/ page

        self.new_post = Post.objects.get(text='Test post again')
        response_edit = self.login_client.get(reverse('post', kwargs={'username': self.user.username, 'post_id': self.new_post.pk}))
        self.assertContains(response_edit, 'Test post again')  # Check if new post added to /profile/post_id page

    def test_edit_post(self):
        self.post = Post.objects.get(id=self.post.id)
        self.post.text = 'Test post after update'
        self.post.save()

        time.sleep(20)  # 20 seconds wait because index page is cached

        response_index = self.login_client.get(reverse('index'))
        self.assertContains(response_index, 'Test post after update')  # Check if post was edited on index page

        response_profile = self.login_client.get(reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(response_profile, 'Test post after update')  # Check if post was edited on /profile page

        response_edit = self.login_client.get(reverse('post', kwargs={'username': self.user.username, 'post_id': self.post.pk}))
        self.assertContains(response_edit, 'Test post after update')  # Check if post was edited on /profile/post_id page

        response_group = self.login_client.get(reverse('group', args=[self.group.slug]))
        self.assertContains(response_group, 'Test post after update')  # Check if post was edited on /group page_number

    def test_unauthorized(self):
        posts_count = Post.objects.count()
        new_post_data = {'text': 'Test post', 'author': 'anonymous'}
        response = self.logout_client.post(reverse('new_post'), new_post_data)
        login_page = '/auth/login/?next=/new/'
        self.assertEqual(response['location'], login_page)  # Check if redirect goes to login page
        self.assertEqual(response.status_code, 302)  # Check if unauthorized user redirects when trying to use /new/ page
        self.assertEqual(posts_count, Post.objects.count())  # Check if numbers of posts in DB same before and after
                                                             # unauthorized user tried to create a post

    def test_page_not_found(self):
        response = self.logout_client.get('random_url')
        self.assertEqual(response.status_code, 404)  # Check if random url return 404


class TestImages(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testimage', password='testpassword12345', email='testimage@yandex.ru')
        self.client.force_login(self.user)
        self.group = Group.objects.create(title='testgroup', slug='testslug')
        self.post = Post.objects.create(text='Test post', author=self.user, group=self.group)

    def test_images(self):
        with open('media/test.png', 'rb') as img:
            new_post_data = {'text': 'Test post with image', 'author': self.user.username, 'group': self.group.id, 'image': img}
            response = self.client.post(reverse('post_edit', kwargs={'username': self.user.username, 'post_id': self.post.pk}), new_post_data)
            self.assertEqual(response.status_code, 302)  # Check editing post with image and redirecting after

        time.sleep(20)  # 20 seconds wait because index page is cached

        response_index = self.client.get(reverse('index'))
        self.assertContains(response_index, 'img')  # Check img tag from created post on index page

        response_profile = self.client.get(reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(response_profile, 'img')  # Check img tag from created post on /profile page

        response_group = self.client.get(reverse('group', args=[self.group.slug]))
        self.assertContains(response_group, 'img')  # Check img tag from created post on /group page

        response_edit = self.client.get(reverse('post', kwargs={'username': self.user.username, 'post_id': self.post.pk}))
        self.assertContains(response_edit, 'img')  # Check img tag from created post on /profile/post_id page

    def test_wrong_file(self):
        with open('media/random_test.txt', 'rb') as img:
            new_post_data = {'text': 'Test post with wrong file', 'author': self.user.username, 'group': self.group.id, 'image': img}
            response = self.client.post(reverse('new_post'), new_post_data)
            self.assertEqual(response.status_code, 200)  # Check creating new post with wrong file. If not redirecting, form is not valid


class TestCache(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testimage', password='testpassword12345', email='testimage@yandex.ru')
        self.client.force_login(self.user)
        self.group = Group.objects.create(title='testgroup', slug='testslug')

    def test_cache(self):
        first_post_data = {'text': 'Test post 1', 'author': self.user.username, 'group': self.group.id}
        second_post_data = {'text': 'Test post 2', 'author': self.user.username, 'group': self.group.id}

        self.client.post(reverse('new_post'), first_post_data, follow=True)
        response_index1 = self.client.get(reverse('index'))
        self.assertContains(response_index1, 'Test post 1')  # Check if first post was added to index cached page

        self.client.post(reverse('new_post'), second_post_data, follow=True)
        response_index2 = self.client.get(reverse('index'))
        self.assertNotContains(response_index2, 'Test post 2')  # Check that we can't find second post on index cached page

        time.sleep(20)  # Wait 20 second before next cache
        response_index2 = self.client.get(reverse('index'))
        self.assertContains(response_index2, 'Test post 2')  # Check if second post was added to index cached page after new cache happend


class TestFollow(TestCase):
    def setUp(self):
        self.login_client = Client()
        self.logout_client = Client()
        self.logout_client.logout()
        self.user1 = User.objects.create_user(username='test1', password='testpassword1', email='test1@yandex.ru')
        self.user2 = User.objects.create_user(username='test2', password='testpassword2', email='test2@yandex.ru')
        self.user3 = User.objects.create_user(username='test3', password='testpassword3', email='test3@yandex.ru')
        self.user4 = User.objects.create_user(username='test4', password='testpassword4', email='test4@yandex.ru')
        self.user5 = User.objects.create_user(username='test5', password='testpassword5', email='test5@yandex.ru')
        self.login_client.force_login(self.user1)
        self.group = Group.objects.create(title='testgroup', slug='testslug')

    def test_follow(self):

        self.login_client.get(reverse('profile_follow', kwargs={'username': self.user2.username}))
        self.login_client.get(reverse('profile_follow', kwargs={'username': self.user3.username}))
        self.login_client.get(reverse('profile_follow', kwargs={'username': self.user4.username}))
        self.login_client.get(reverse('profile_follow', kwargs={'username': self.user5.username}))

        self.assertEqual(self.user1.follower.count(), 4)  # Check if authorized user following 4 users

        self.login_client.get(reverse('profile_unfollow', kwargs={'username': self.user2.username}))
        self.login_client.get(reverse('profile_unfollow', kwargs={'username': self.user3.username}))
        self.login_client.get(reverse('profile_unfollow', kwargs={'username': self.user4.username}))
        self.login_client.get(reverse('profile_unfollow', kwargs={'username': self.user5.username}))

        self.assertEqual(self.user1.follower.count(), 0)  # Check if authorized user unfollowed 4

    def test_feed(self):
        self.login_client.force_login(self.user5)
        self.post = Post.objects.create(text='Test post from User5', author=self.user5, group=self.group)

        self.login_client.force_login(self.user1)
        self.login_client.get(reverse('profile_follow', kwargs={'username': self.user5.username}))
        response = self.login_client.get(reverse('follow_index'))
        self.assertContains(response, 'Test post from User5')  # Check feed for user1 who followed user5

        self.login_client.force_login(self.user2)
        response = self.login_client.get(reverse('follow_index'))
        self.assertNotContains(response, 'Test post from User5')  # Check feed for user2 who didn't follow user5
                                                                  # and can't see his post

    def test_comment(self):
        self.post = Post.objects.create(text='Test post from User5', author=self.user5, group=self.group)
        self.login_client.force_login(self.user1)
        comment_data1 = {'text': 'Comment from authorized user'}
        self.login_client.post(reverse('add_comment', kwargs={
                                                            'username': self.user5.username,
                                                            'post_id': self.post.id
                                                            }), comment_data1)
        response = self.login_client.get(reverse('add_comment', kwargs={
                                                            'username': self.user5.username,
                                                            'post_id': self.post.id
                                                            }), follow=True)

        self.assertContains(response, 'Comment from authorized user')  # Check if comment from authorized user was added

        comment_data2 = {'text': 'Comment from unauthorized user'}
        self.logout_client.post(reverse('add_comment', kwargs={
                                                                'username': self.user5.username,
                                                                'post_id': self.post.id}),
                                                                comment_data2)
        response = self.logout_client.get(reverse('add_comment', kwargs={
                                                            'username': self.user5.username,
                                                            'post_id': self.post.id
                                                            }), follow=True)

        self.assertNotContains(response, 'Comment from unauthorized user')  # Check that comment from unauthorized user was not added
