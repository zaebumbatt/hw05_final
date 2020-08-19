import os
import tempfile
import time

from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from posts.models import Group, Post, User


class TestPosts(TestCase):
    def setUp(self):
        self.login_client = Client()
        self.logout_client = Client()
        self.user = User.objects.create_user(
            username='test',
            password='testpassword12345',
            email='test@yandex.ru'
        )
        self.login_client.force_login(self.user)
        self.logout_client.logout()
        self.posts_count = Post.objects.count()
        self.group = Group.objects.create(
            title='testgroup',
            slug='testslug'
        )
        self.post = Post.objects.create(
            text='Test post',
            author=self.user,
            group=self.group
        )

    def test_new_post(self):
        """Check if authorized user can create post
        and it appeared on index, profile and post pages"""
        new_post_data = {
            'text': 'Test post again',
            'author': self.user.username,
            'group': self.group.id
        }
        response = self.login_client.post(
            reverse('new_post'),
            new_post_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        time.sleep(20)

        response_index = self.login_client.get(reverse('index'))
        self.assertContains(response_index, 'Test post again')

        kwargs = {'username': self.user.username}
        response_profile = self.login_client.get(
            reverse('profile', kwargs=kwargs)
        )
        self.assertContains(response_profile, 'Test post again')

        self.new_post = Post.objects.get(text='Test post again')
        kwargs = {'username': self.user.username, 'post_id': self.new_post.pk}
        response_edit = self.login_client.get(reverse('post', kwargs=kwargs))
        self.assertContains(response_edit, 'Test post again')

    def test_edit_post(self):
        """Check if post was edited on index, profile, post and group pages"""
        self.post = Post.objects.get(id=self.post.id)
        self.post.text = 'Test post after update'
        self.post.save()

        time.sleep(20)

        response_index = self.login_client.get(reverse('index'))
        self.assertContains(response_index, 'Test post after update')

        kwargs = {'username': self.user.username}
        response_profile = self.login_client.get(
            reverse('profile', kwargs=kwargs)
        )
        self.assertContains(response_profile, 'Test post after update')

        kwargs = {'username': self.user.username, 'post_id': self.post.pk}
        response_edit = self.login_client.get(reverse('post', kwargs=kwargs))
        self.assertContains(response_edit, 'Test post after update')

        response_group = self.login_client.get(
            reverse('group', args=[self.group.slug])
        )
        self.assertContains(response_group, 'Test post after update')

    def test_unauthorized(self):
        """Check that unauthorized user can't create post
        and being redirected to login page"""
        posts_count = Post.objects.count()
        new_post_data = {'text': 'Test post', 'author': 'anonymous'}
        response = self.logout_client.post(reverse('new_post'), new_post_data)
        login_page = '/auth/login/?next=/new/'
        self.assertEqual(response['location'], login_page)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(posts_count, Post.objects.count())

    def test_page_not_found(self):
        response = self.logout_client.get('random_url')
        self.assertEqual(response.status_code, 404)


class TestImages(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testimage',
            password='testpassword12345',
            email='testimage@yandex.ru'
        )
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            title='testgroup',
            slug='testslug'
        )
        self.post = Post.objects.create(
            text='Test post',
            author=self.user,
            group=self.group
        )

    def test_images(self):
        """Check adding image to post
        and if it appeared on index, profile, group and post pages"""
        img = Image.new('RGB', (60, 30), color='red')
        img.save('media/pil_red.png')
        with open('media/pil_red.png', 'rb') as img:
            new_post_data = {
                'text': 'Test post with image',
                'author': self.user.username,
                'group': self.group.id,
                'image': img
            }
            kwargs = {'username': self.user.username, 'post_id': self.post.pk}
            response = self.client.post(
                reverse('post_edit', kwargs=kwargs),
                new_post_data
            )
            self.assertEqual(response.status_code, 302)

        time.sleep(20)

        response_index = self.client.get(reverse('index'))
        self.assertContains(response_index, 'img')

        kwargs = {'username': self.user.username}
        response_profile = self.client.get(reverse('profile', kwargs=kwargs))
        self.assertContains(response_profile, 'img')

        response_group = self.client.get(
            reverse('group', args=[self.group.slug])
        )
        self.assertContains(response_group, 'img')

        kwargs = {'username': self.user.username, 'post_id': self.post.pk}
        response_edit = self.client.get(reverse('post', kwargs=kwargs))
        self.assertContains(response_edit, 'img')

        os.remove('media/pil_red.png')

    def test_wrong_file(self):
        with tempfile.TemporaryFile() as img:
            new_post_data = {
                'text': 'Test post with wrong file',
                'author': self.user.username,
                'group': self.group.id,
                'image': img
            }
            response = self.client.post(reverse('new_post'), new_post_data)
            self.assertEqual(response.status_code, 200)


class TestCache(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testimage',
            password='testpassword12345',
            email='testimage@yandex.ru'
        )
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            title='testgroup',
            slug='testslug'
        )

    def test_cache(self):
        """Check if cache work on index page"""
        first_post_data = {
            'text': 'Test post 1',
            'author': self.user.username,
            'group': self.group.id
        }
        second_post_data = {
            'text': 'Test post 2',
            'author': self.user.username,
            'group': self.group.id
        }

        self.client.post(reverse('new_post'), first_post_data, follow=True)
        response_index1 = self.client.get(reverse('index'))
        self.assertContains(response_index1, 'Test post 1')

        self.client.post(reverse('new_post'), second_post_data, follow=True)
        response_index2 = self.client.get(reverse('index'))
        self.assertNotContains(response_index2, 'Test post 2')

        time.sleep(20)
        response_index2 = self.client.get(reverse('index'))
        self.assertContains(response_index2, 'Test post 2')


class TestFollow(TestCase):
    """Check follow/unfollow, feed and comments"""

    def setUp(self):
        self.login_client = Client()
        self.logout_client = Client()
        self.logout_client.logout()
        self.user1 = User.objects.create_user(
            username='test1',
            password='testpassword1',
            email='test1@yandex.ru'
        )
        self.user2 = User.objects.create_user(
            username='test2',
            password='testpassword2',
            email='test2@yandex.ru'
        )
        self.user3 = User.objects.create_user(
            username='test3',
            password='testpassword3',
            email='test3@yandex.ru'
        )
        self.user4 = User.objects.create_user(
            username='test4',
            password='testpassword4',
            email='test4@yandex.ru'
        )
        self.user5 = User.objects.create_user(
            username='test5',
            password='testpassword5',
            email='test5@yandex.ru'
        )
        self.login_client.force_login(self.user1)
        self.group = Group.objects.create(title='testgroup', slug='testslug')

    def test_follow(self):
        kwargs = {'username': self.user2.username}
        self.login_client.get(reverse('profile_follow', kwargs=kwargs))

        kwargs = {'username': self.user3.username}
        self.login_client.get(reverse('profile_follow', kwargs=kwargs))

        kwargs = {'username': self.user4.username}
        self.login_client.get(reverse('profile_follow', kwargs=kwargs))

        kwargs = {'username': self.user5.username}
        self.login_client.get(reverse('profile_follow', kwargs=kwargs))

        self.assertEqual(self.user1.follower.count(), 4)

    def test_unfollow(self):
        kwargs = {'username': self.user2.username}
        self.login_client.get(reverse('profile_unfollow', kwargs=kwargs))

        kwargs = {'username': self.user3.username}
        self.login_client.get(reverse('profile_unfollow', kwargs=kwargs))

        kwargs = {'username': self.user4.username}
        self.login_client.get(reverse('profile_unfollow', kwargs=kwargs))

        kwargs = {'username': self.user5.username}
        self.login_client.get(reverse('profile_unfollow', kwargs=kwargs))

        self.assertEqual(self.user1.follower.count(), 0)

    def test_feed(self):
        self.login_client.force_login(self.user5)
        self.post = Post.objects.create(
            text='Test post from User5',
            author=self.user5,
            group=self.group
        )

        self.login_client.force_login(self.user1)
        kwargs = {'username': self.user5.username}
        self.login_client.get(reverse('profile_follow', kwargs=kwargs))
        response = self.login_client.get(reverse('follow_index'))
        self.assertContains(response, 'Test post from User5')

        self.login_client.force_login(self.user2)
        response = self.login_client.get(reverse('follow_index'))
        self.assertNotContains(response, 'Test post from User5')

    def test_comment(self):
        self.post = Post.objects.create(
            text='Test post from User5',
            author=self.user5,
            group=self.group
        )
        self.login_client.force_login(self.user1)

        kwargs = {'username': self.user5.username, 'post_id': self.post.id}
        comment_data1 = {'text': 'Comment from authorized user'}
        self.login_client.post(
            reverse('add_comment', kwargs=kwargs),
            comment_data1
        )

        response = self.login_client.get(
            reverse('add_comment', kwargs=kwargs),
            follow=True
        )
        self.assertContains(response, 'Comment from authorized user')

        comment_data2 = {'text': 'Comment from unauthorized user'}
        self.logout_client.post(
            reverse('add_comment', kwargs=kwargs),
            comment_data2
        )

        response = self.logout_client.get(
            reverse('add_comment', kwargs=kwargs),
            follow=True
        )
        self.assertNotContains(response, 'Comment from unauthorized user')
