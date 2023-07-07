import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def read_config() -> yaml:
    with open("./auth.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)

    return config


def authenticate() -> list:
    config = read_config()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        config["preauthorized"],
    )

    name, authentication_status, username = authenticator.login("Login", "main")

    return authenticator, authentication_status


def logout(authenticator) -> None:
    authenticator.logout("Logout", "main", key="unique_key")


# hashed_passwords = stauth.Hasher(["Nick"]).generate()

# print(hashed_passwords)
