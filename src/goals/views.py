from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from goals.filters import GoalDateFilter
from goals.models import Board, Goal, GoalCategory, GoalComment
from goals.permissions import (BoardPermission, CommentsPermissions,
                               GoalCategoryPermissions, GoalPermissions,
                               IsOwnerOrReadOnly)
from goals.serializers import (BoardCreateSerializer, BoardListSerializer,
                               BoardSerializer, GoalCategoryCreateSerializer,
                               GoalCategorySerializer,
                               GoalCommentCreateSerializer,
                               GoalCommentSerializer, GoalCreateSerializer,
                               GoalSerializer)


class BoardCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardCreateSerializer


class BoardListView(generics.ListAPIView):
    model = Board
    permission_classes = [BoardPermission]
    serializer_class = BoardListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['title']
    ordering = ['title']

    def get_queryset(self):
        return Board.objects.prefetch_related('participants').filter(
            participants__user_id=self.request.user.id,
            is_deleted=False
        )


class BoardView(generics.RetrieveUpdateDestroyAPIView):
    model = Board
    permission_classes = [BoardPermission]
    serializer_class = BoardSerializer

    def get_queryset(self):
        return Board.objects.prefetch_related('participants').filter(
            participants__user_id=self.request.user.id,
            is_deleted=False
        )

    def perform_destroy(self, instance: Board):
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted', ))
            instance.categories.update(is_deleted=True)
            Goal.objects.filter(category__board=instance).update(
                status=Goal.Status.archived
            )
        return instance


class GoalCategoryCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategoryCreateSerializer


class GoalCategoryListView(generics.ListAPIView):
    model = GoalCategory
    permission_classes = [GoalCategoryPermissions]
    serializer_class = GoalCategorySerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['board']
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title']

    def get_queryset(self):
        return GoalCategory.objects.prefetch_related('board__participants').filter(
            board__participants__user_id=self.request.user.id,
            is_deleted=False
        )


class GoalCategoryView(generics.RetrieveUpdateDestroyAPIView):
    model = GoalCategory
    serializer_class = GoalCategorySerializer
    permission_classes = [GoalCategoryPermissions, IsOwnerOrReadOnly]

    def get_queryset(self):
        return GoalCategory.objects.prefetch_related('board__participants').filter(
            board__participants__user_id=self.request.user.id,
            is_deleted=False
        )

    def perform_destroy(self, instance: GoalCategory):
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted',))
            Goal.objects.filter(category=instance).update(status=Goal.Status.archived)
        return instance


class GoalCreateView(generics.CreateAPIView):
    serializer_class = GoalCreateSerializer
    permission_classes = [GoalPermissions]


class GoalListView(generics.ListAPIView):
    model = Goal
    permission_classes = [GoalPermissions]
    serializer_class = GoalSerializer
    filterset_class = GoalDateFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title', 'descriptions']

    def get_queryset(self):
        return Goal.objects.select_related('user', 'category__board').filter(
            Q(category__board__participants__user_id=self.request.user.id) & ~Q(status=Goal.Status.archived)
        )


class GoalView(generics.RetrieveUpdateDestroyAPIView):
    model = Goal
    permission_classes = [GoalPermissions, IsOwnerOrReadOnly]
    serializer_class = GoalSerializer

    def get_queryset(self):
        return Goal.objects.select_related('user', 'category__board').filter(
            Q(category__board__participants__user_id=self.request.user.id) & ~Q(status=Goal.Status.archived)
        )

    def perform_destroy(self, instance: Goal):
        instance.status = Goal.Status.archived
        instance.save(update_fields=('status',))
        return instance


class GoalCommentCreateView(generics.CreateAPIView):
    serializer_class = GoalCommentCreateSerializer
    permission_classes = [CommentsPermissions]


class GoalCommentListView(generics.ListAPIView):
    model = GoalComment
    permission_classes = [CommentsPermissions]
    serializer_class = GoalCommentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['goal']
    ordering = ['-created']

    def get_queryset(self):
        return GoalComment.objects.select_related('goal__category__board', 'user').filter(
            goal__category__board__participants__user_id=self.request.user.id
        )


class GoalCommentView(generics.RetrieveUpdateDestroyAPIView):
    model = GoalComment
    permission_classes = [CommentsPermissions, IsOwnerOrReadOnly]
    serializer_class = GoalCommentSerializer

    def get_queryset(self):
        return GoalComment.objects.select_related('goal__category__board', 'user').filter(
            goal__category__board__participants__user_id=self.request.user.id
        )
