from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from post.models import Post

User = get_user_model()

class PostUploadTestCase(TestCase):

    def setUp(self):
        # Create a test user with an email address
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )

    def test_post_create(self):
        # Log in the test user
        self.client.login(username='testuser', password='testpassword')

        # Create a sample post with an image
        image_file = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        
        # Use the correct view name to get the URL for creating a post
        response = self.client.post(reverse('create_post'), {
            'title': 'Test Post',
            'content': 'This is a test post.',
            'image': image_file,
        })

        # Test that the response code is correct (200 OK)
        self.assertEqual(response.status_code, 200)

        # Test that the post instance is created
        self.assertEqual(Post.objects.count(), 1)

        # Validate that the image is stored correctly
        post = Post.objects.first()
        self.assertTrue(post.image.url.endswith('test_image.jpg'))
