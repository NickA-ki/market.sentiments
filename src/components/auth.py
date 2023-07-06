import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def authenticate() -> list:
    with open("./auth.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        config["preauthorized"],
    )

    name, authentication_status, username = authenticator.login("Login", "main")

    return authenticator, authentication_status


def logout() -> None:
    authenticator, authentication_status = authenticate()
    authenticator.logout("Logout", "main", key="unique_key")


# hashed_passwords = stauth.Hasher(["Nick"]).generate()

# print(hashed_passwords)
