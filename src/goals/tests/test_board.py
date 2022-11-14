from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User
from goals.models import Board, BoardParticipant


class BoardCreateTestCase(APITestCase):

    def setUp(self) -> None:
        self.url = reverse('create-board')

    def test_auth_required(self):
        response = self.client.post(self.url, {'title': 'board title'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success(self):
        user = User.objects.create_user(username='test_user', password='test_password')
        self.client.force_login(user)
        self.assertFalse(Board.objects.exists())
        self.assertFalse(BoardParticipant.objects.exists())
        response = self.client.post(self.url, {'title': 'board title'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_board: Board = Board.objects.last()
        self.assertDictEqual(
            response.json(),
            {
                'id': new_board.id,
                'created': timezone.localtime(new_board.created).isoformat(),
                'updated': timezone.localtime(new_board.updated).isoformat(),
                'title': 'board title',
                'is_deleted': False,
            }
        )
        board_participans = BoardParticipant.objects.filter(
            board=new_board,
            user=user,
        ).all()
        self.assertEqual(len(board_participans), 1)
        self.assertEqual(board_participans[0].role, BoardParticipant.Role.owner)


class BoardRetrieve(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test_user', password='test_password')
        self.board = Board.objects.create(title='board_title')
        BoardParticipant.objects.create(board=self.board, user=self.user, role=BoardParticipant.Role.owner)

    @parameterized.expand([
        ('owner', BoardParticipant.Role.owner),
        ('writer', BoardParticipant.Role.writer),
        ('reader', BoardParticipant.Role.reader),
    ])
    def test_success(self, _, role: BoardParticipant.Role):
        new_user = User.objects.create_user(username='new_test_user', password='test_password')
        if role is BoardParticipant.Role.owner:
            self.client.force_login(self.user)
        else:
            self.client.force_login(new_user)
            if role:
                BoardParticipant.objects.create(board=self.board, user=new_user, role=role)

        response = self.client.get(reverse('retrieve-update-destroy-board', kwargs={'pk': self.board.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_not_participant(self):
        new_user = User.objects.create_user(username='new_test_user', password='test_password')
        self.client.force_login(new_user)

        response = self.client.get(reverse('retrieve-update-destroy-board', kwargs={'pk': self.board.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_deleted_board(self):
        self.board.is_deleted = True
        self.board.save(update_fields=('is_deleted', ))
        self.client.force_login(self.user)

        response = self.client.get(reverse('retrieve-update-destroy-board', kwargs={'pk': self.board.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_auth_required(self):
        response = self.client.get(reverse('retrieve-update-destroy-board', kwargs={'pk': self.board.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BoardListTestCase(APITestCase):

    def test_auth_required(self):
        response = self.client.get(reverse('list-boards'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success(self):
        user = User.objects.create_user(username='new_test_user', password='test_password')

        boards = Board.objects.bulk_create([
            Board(title='board_3'),
            Board(title='board_1'),
            Board(title='board_2'),
        ])
        boards.append(Board.objects.create(title='board_4', is_deleted=True))

        BoardParticipant.objects.bulk_create([
            BoardParticipant(board=board, user=user)
            for board in boards
        ])
        self.client.force_login(user)

        response = self.client.get(reverse('list-boards'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        board_list = response.json()
        self.assertTrue(isinstance(board_list, list))
        self.assertListEqual(
            [board['title'] for board in board_list],
            ['board_1', 'board_2', 'board_3']
        )
#
#     def test_success_deleted(self):
#         user = User.objects.create_user(username='new_test_user', password='test_password')
#         board = Board.objects.create(title='board_deleted', is_deleted=True)
#         BoardParticipant.objects.create(board=board, user=user)
#         self.client.force_login(user)
#
#         response = self.client.get(reverse('list-boards'))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         board_list = response.json()
#         self.assertListEqual(board_list, [])
#
#
# class CategoryTestCase(APITestCase):
#
#     def setUp(self) -> None:
#         self.user = User.objects.create_user(
#             username='test_user',
#             password='test_password'
#         )
#         self.board = Board.objects.create(title='board_title')
#         BoardParticipant.objects.create(board=self.board, user=self.user, role=BoardParticipant.Role.owner)
#
#     def test_create_category(self):
#         url = reverse('create-category')
#         self.client.force_login(self.user)
#         response = self.client.post(url, {'title': 'category title', 'is_deleted': False, 'board': self.board.id})
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#         new_category: GoalCategory = GoalCategory.objects.last()
#         self.assertDictEqual(
#             response.json(),
#             {
#                 'id': new_category.id,
#                 'created': timezone.localtime(new_category.created).isoformat(),
#                 'updated': timezone.localtime(new_category.updated).isoformat(),
#                 'title': 'category title',
#                 'is_deleted': False,
#                 'board': new_category.board.id,
#             }
#         )
#
#     def test_add_category_board(self):
#         url = reverse('create-category')
#
#         user_1 = User.objects.create_user(
#             username='test_user_1',
#             password='test_password_1'
#         )
#
#         user_2 = User.objects.create_user(
#             username='test_user_2',
#             password='test_password_2'
#         )
#
#         user_3 = User.objects.create_user(
#             username='test_user_3',
#             password='test_password_3'
#         )
#
#         board = Board.objects.create(title='board_title_test')
#         BoardParticipant.objects.create(board=board, user=user_1, role=BoardParticipant.Role.owner)
#         BoardParticipant.objects.create(board=board, user=user_2, role=BoardParticipant.Role.writer)
#         BoardParticipant.objects.create(board=board, user=user_3, role=BoardParticipant.Role.reader)
#
#         self.client.force_login(user_1)
#         response = self.client.post(url, {'title': 'category title_user1', 'is_deleted': False, 'board': board.id})
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#         self.client.force_login(user_2)
#         response = self.client.post(url, {'title': 'category title_user2', 'is_deleted': False, 'board': board.id})
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#         self.client.force_login(user_3)
#         response = self.client.post(url, {'title': 'category title_user3', 'is_deleted': False, 'board': board.id})
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
