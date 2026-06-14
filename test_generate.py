from services import generate_image

if __name__ == '__main__':
    try:
        img = generate_image('', 'a golden goat', '', 'flux', 'square', 30, 7.5)
        print('SUCCESS', type(img), getattr(img, 'size', None))
    except Exception as e:
        print('ERROR', e)
