from django.db import models

# Create your models here.

class HeroPost(models.Model):
    alignments = (
        ("left", "Left aligned"),
        ("right", "Right aligned"),
    )

    eng_title = models.CharField(max_length=25)
    eng_topic = models.CharField(max_length=10)
    eng_description = models.TextField(max_length=350)
    eng_button_text = models.CharField(max_length=15)
    ukr_title = models.CharField(max_length=25)
    ukr_topic = models.CharField(max_length=10)
    ukr_description = models.TextField(max_length=350)
    ukr_button_text = models.CharField(max_length=15)
    button_link = models.TextField()
    image = models.ImageField(upload_to='files/hero_images')
    text_alignment = models.CharField(max_length=5, choices=alignments)

class Event(models.Model):
    categories = (
        (0, "Video release"),
        (1, "Idk, don't pick this"),
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    eng_title = models.CharField(max_length=50)
    ukr_title = models.CharField(max_length=50)
    category = models.SmallIntegerField(choices=categories)
    link = models.TextField()

class Blogpost(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    eng_title = models.CharField(max_length=50)
    eng_markdown_post_text = models.TextField()
    ukr_title = models.CharField(max_length=50)
    ukr_markdown_post_text = models.TextField()
    image = models.ImageField(upload_to='files/blogpost_covers')