from mallo.router import Router


def test_url_for():
    router = Router()

    def user(request, id):
        return f'User {id}'

    router.add_route('/user/<int:id>', user, ['GET'])
    assert router.url_for('user', id=5) == '/user/5'
