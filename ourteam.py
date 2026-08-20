from app_factory import create_app, initialize_database

# Backwards-compatible entry point. New code should call create_app(config).
app = create_app()

if __name__ == '__main__':
    initialize_database(app)
    app.run(host='127.0.0.1', debug=True, port=5002)
