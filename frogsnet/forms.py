from django import forms
from django.contrib.auth.models import User
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from .models import Frog, ForumPost, ForumTopic


class FrogRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class WallPostForm(forms.ModelForm):
    text = forms.CharField(
        label=_('Transmission'),
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'class': 'profile-terminal-field__input',
                'placeholder': _('append_log_message --channel=public...'),
            }
        ),
    )

    class Meta:
        model = ForumPost
        fields = ['text']

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if not text:
            raise forms.ValidationError(_('Transmission text is required.'))
        return text

    def save(self, *, author, topic, commit=True):
        text = self.cleaned_data['text']
        post = ForumPost(
            author=author,
            topic=topic,
            content=text,
            title=Truncator(text).chars(60),
        )
        if commit:
            post.save()
        return post


class ForumPostForm(forms.ModelForm):
    title = forms.CharField(
        label=_('Transmission title'),
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'class': 'forum-terminal-field',
                'placeholder': _('ENTER_TRANSMISSION_SUBJECT...'),
                'autocomplete': 'off',
            }
        ),
    )
    topic = forms.ModelChoiceField(
        queryset=ForumTopic.objects.filter(parent_topic__isnull=True, owner_if_wall__isnull=True).order_by('title'),
        required=False,
        empty_label=_('Select a topic'),
        label=_('Topic directory'),
        widget=forms.Select(attrs={'class': 'forum-terminal-field forum-terminal-field--select'}),
    )
    content = forms.CharField(
        label=_('Payload body'),
        widget=forms.Textarea(
            attrs={
                'class': 'forum-terminal-field forum-terminal-field--textarea',
                'rows': 10,
                'placeholder': _('TYPE_PAYLOAD_HERE... DATA_PACKETS WILL BE COMPRESSED BEFORE DISPATCH.'),
            }
        ),
    )

    class Meta:
        model = ForumPost
        fields = ['title', 'topic', 'content']

    def __init__(self, *args, **kwargs):
        self.forced_topic = kwargs.pop('forced_topic', None)
        super().__init__(*args, **kwargs)

        topic_queryset = ForumTopic.objects.filter(parent_topic__isnull=True, owner_if_wall__isnull=True).order_by('title')
        self.fields['topic'].queryset = topic_queryset
        if self.forced_topic is not None:
            self.fields['topic'].initial = self.forced_topic

    def clean(self):
        cleaned_data = super().clean()
        selected_topic = cleaned_data.get('topic') or self.forced_topic
        if selected_topic is None:
            raise forms.ValidationError({'topic': _('Please select a forum topic.')})
        cleaned_data['topic'] = selected_topic
        return cleaned_data

    def save(self, *, author, commit=True):
        post = super().save(commit=False)
        post.author = author
        post.response_to = None
        post.topic = self.cleaned_data['topic']
        if commit:
            post.save()
        return post


class FrogProfileEditForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'terminal-form-input'}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'terminal-form-input'}))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'terminal-form-textarea'}))
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'profile-edit-avatar-input',
            'accept': 'image/*',
            'aria-label': _('Profile avatar'),
        }),
    )
    clear_avatar = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_clear_avatar', 'value': ''}),
    )
    minecraft_username = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'terminal-form-input'}))
    location = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'terminal-form-input'}))
    show_real_name = forms.ChoiceField(
        choices=[('public', _('PUBLIC')), ('squad_only', _('SQUAD_ONLY')), ('classified', _('CLASSIFIED'))],
        initial='public',
        required=False,
        widget=forms.RadioSelect,
    )
    current_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    show_active_modpacks = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'terminal-form-checkbox'}))
    show_last_played_server = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'terminal-form-checkbox'}))
    allow_friend_requests = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'terminal-form-checkbox'}))
    show_achievements = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'terminal-form-checkbox'}))
    allow_external_wall_posts = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'terminal-form-checkbox'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('instance', None)
        self.frog = kwargs.pop('frog', None)
        super().__init__(*args, **kwargs)

        if self.user is None:
            self.user = getattr(self, 'instance', None)

        if self.user is not None:
            self.fields['username'].initial = self.user.username
            self.fields['first_name'].initial = self.user.first_name

        if self.frog is None and self.user is not None:
            self.frog = getattr(self.user, 'frog', None)

        if self.frog is not None:
            self.fields['bio'].initial = self.frog.bio
            self.fields['minecraft_username'].initial = self.frog.minecraft_username
            self.fields['location'].initial = self.frog.location
            self.fields['show_real_name'].initial = self.frog.show_real_name or 'public'
            self.fields['show_active_modpacks'].initial = self.frog.show_active_modpacks
            self.fields['show_last_played_server'].initial = self.frog.show_last_played_server
            self.fields['allow_friend_requests'].initial = self.frog.allow_friend_requests
            self.fields['show_achievements'].initial = self.frog.show_achievements
            self.fields['allow_external_wall_posts'].initial = self.frog.allow_external_wall_posts

        if self.initial:
            for field_name, value in self.initial.items():
                if field_name in self.fields and self.fields[field_name].initial is None:
                    self.fields[field_name].initial = value

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError(_('Username is required.'))
        if self.user is not None and User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError(_('That username is already in use.'))
        return username

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password', '')
        new_password = cleaned_data.get('new_password', '')
        confirm_password = cleaned_data.get('confirm_password', '')

        if current_password or new_password or confirm_password:
            if self.user is None or not self.user.check_password(current_password):
                raise forms.ValidationError(_('Current password is incorrect.'))

            if not new_password:
                raise forms.ValidationError(_('Please enter a new password.'))
            if not confirm_password:
                raise forms.ValidationError(_('Please confirm the new password.'))
            if new_password != confirm_password:
                raise forms.ValidationError(_('New passwords do not match.'))

        return cleaned_data

    def save(self, commit=True):
        if self.user is None:
            raise ValueError('A user instance is required to save the profile edit form.')

        self.user.username = self.cleaned_data['username']
        self.user.first_name = self.cleaned_data['first_name'] or ''
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            self.user.set_password(new_password)
        if commit:
            self.user.save()

        frog = self.frog or getattr(self.user, 'frog', None)
        if frog is None:
            frog = Frog.objects.create(user=self.user)

        frog.bio = self.cleaned_data.get('bio', '')
        frog.minecraft_username = self.cleaned_data.get('minecraft_username', '')
        frog.location = self.cleaned_data.get('location', '')
        selected_visibility = self.cleaned_data.get('show_real_name') or 'public'
        frog.show_real_name = selected_visibility
        frog.show_active_modpacks = self.cleaned_data.get('show_active_modpacks', True)
        frog.show_last_played_server = self.cleaned_data.get('show_last_played_server', True)
        frog.allow_friend_requests = self.cleaned_data.get('allow_friend_requests', True)
        frog.show_achievements = self.cleaned_data.get('show_achievements', True)
        frog.allow_external_wall_posts = self.cleaned_data.get('allow_external_wall_posts', True)

        avatar = self.cleaned_data.get('avatar')
        if self.cleaned_data.get('clear_avatar'):
            frog.avatar = None
        elif avatar:
            frog.avatar = avatar

        if commit:
            frog.save()
        return self.user