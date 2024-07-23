## SQLAdmin with Access to Data from Third-party APIs

SQLAdmin (https://github.com/aminalaee/sqladmin) is a popular admin library for FastAPI and other frameworks. It works perfectly with databases, but sometimes we need to add information from third-party services to the admin panel. For example, this may be relevant when dealing with microservices that provide a Backend For Frontend (BFF) pattern with admin endpoints.

The main idea of this solution is very simple and naive: override the BaseView and Admin classes from SQLAdmin to make requests to an API instead of making queries to the database.

### The Repo Consists off:

- Service A (FastAPI with an SQLAdmin admin panel)
- Service B (FastAPI third-party service with Book endpoints)

### Setting up
First of all define your custom admin class by inheriting from `api.admin.custom_baseview.APIBaseView`.
Don't forget to define `urls` for API endpoints and override at least the `list` method with the `expose` decorator (it's essential to add your custom class to the Admin Panel menu).

That's almost all!

You can also add labels to fields, limit fields manually, or define your own `wtforms.Form` for create/update methods (if you don't do this, forms will be constructed from `openapi.json` and their functionality will be very limited).

By default, the token to access the third-party API is received from the session.

By default, the list endpoint is expected to return data in the following format (you can override this behavior in `APIBaseView.make_pagination`):
        {
            "objects": [
                {
                "id": 1,
                ...
                }
            ],
            "total_count": 1
        }

### Basic Commands

1. Start services:`./start.sh`
2. Access the admin panel at: `http://127.0.0.1:8000/service-a/admin/`
3. Service B Swagger is available here: `http://127.0.0.1:8001/service-b/docs`

### Foreword

I can't say that this solution is great and elegant, but maybe it will be useful for someone.
