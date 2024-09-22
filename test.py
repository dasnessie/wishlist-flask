def decoratorFactory(name):
    def decorator(f):
        def wrapper():
            print("Before" + name)
            f()
            print("After" + name)

        return wrapper

    return decorator


@decoratorFactory(name="hi")
def foo():
    print("DURING")
    pass


foo()
