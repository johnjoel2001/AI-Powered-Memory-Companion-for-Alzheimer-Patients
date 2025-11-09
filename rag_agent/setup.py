from setuptools import setup, find_packages

setup(
    name="memerai-backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "supabase>=2.0.0",
        "python-dotenv>=1.0.0",
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
    ],
)
