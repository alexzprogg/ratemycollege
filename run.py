from app import create_app # This imports  create_app function from app package defined __init__.py.

app = create_app()

if __name__ == "__main__": # "__main__" is just a string Python uses to indicate the main program file.
    app.run(debug=True)
# The app.run() method starts the Flask application server.