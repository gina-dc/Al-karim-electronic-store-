from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "login_attempts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "source_hash" VARCHAR(64) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_login_attem_source__69a654" ON "login_attempts" ("source_hash");
CREATE INDEX IF NOT EXISTS "idx_login_attem_created_fae3e2" ON "login_attempts" ("created_at");
CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "username" VARCHAR(100) NOT NULL UNIQUE,
    "display_name" VARCHAR(150) NOT NULL,
    "password_hash" VARCHAR(255) NOT NULL,
    "role" VARCHAR(20) NOT NULL,
    "active" BOOL NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS "audit_logs" (
    "id" UUID NOT NULL PRIMARY KEY,
    "action" VARCHAR(100) NOT NULL,
    "details" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "sessions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "token_hash" VARCHAR(64) NOT NULL UNIQUE,
    "csrf_hash" VARCHAR(64) NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_sessions_expires_6bcc94" ON "sessions" ("expires_at");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmm1v6jYUgP9K5E+d1FWFC71XaJoElOpyL4WpwDbdaYpMYoJVY6e20xZ1/e+TnYS8wg"
    "grbxFfKnpeEuc5ds6xc97AnNmIiKumZ2PZYw5oGG+AwjkCDSOjuzQAdN1IowQSTog2hsrK"
    "JMzRYjgRkkNLgoYxhUSgSwPYSFgcuxIzChoG9QhRQmYJyTF1IpFH8ZOHTMkcJGeIg4bx19"
    "+XBsDURq9IhP+6j+YUI2InBoxtdW8tN+XC1bLxuHt7py3V7SamxYg3p5G1u5AzRpfmnoft"
    "K+WjdA6iiEOJ7NhjqFEGzxyK/BGDhiG5h5ZDtSOBjabQIwoG+GXqUUsxMPSd1J/ar8HQYm"
    "am2R+MzGFnZJqgADuLUcUdU6lAvb37142AaClQN2h/bT5cfLr5SSNgQjpcKzUu8K4doYS+"
    "q4YeUYZ6/FnS7Rnk+aQjjxRtIfk2nENBBDqaZCHCENIOsII5fDUJoo6cgYZRub5ew/n35o"
    "NGXbm+1qwZh5a/YPqBqurrFPOIsY0kxP4KS0L+Nhz08yHHXFKUbWxJ4x+DYCF3RTs2ryce"
    "JhJTcaVue4iprRCpK8+FeCJx0hf3zT/TQWj3Bq30GlAXaKUCYnGkkJlQZmNyCyWSeI7y45"
    "L0TIcmcL0Kf5zicuAI2gNKFsELb01oRt37znDUvP8tEZ/b5qijNFUtXaSkFzepmC0vYvzR"
    "HX011L/Gj0G/kw7j0m70A6gxQU8yk7IXE9qxd3MoDaklou4JxM1iWSXm8j9SSzC4Ywnx9o"
    "lE5erpY24eUaSyZO8YR9ih39FC8+1SISG1UA7PoDwZB5c5SaKRNBoihy/L2iY+nRg1bUSQ"
    "1A8/7IyM/rjXA5rwBFqPL5DbZgK10rAqS0mWtlnVvDpPSyCFjqajHkMNOqDeYw6mTSnR3J"
    "V5RWNCv7ZwJMrShL7puXgsefEomMctZM6gmBWpIFNuuyojM8j3VkXe1DYoIm9qK2tIpTrl"
    "imWv5MtVsGRS7GEywhAJ4QcikwxC1do8IHyjcwYoeQaQ7BHRwgkg6fUx7///5n3Kr3/Bp4"
    "UpJ5xKeFbz8ZjRq4s5Eltk2aRn+bLsiWTVENLac4DTqqXOpz8nfvpzbDEuwfHPkSLd+vyn"
    "3Ry2m7edQx3/aOo5lX4YjdVlvnqgc41f8hpfBVn/LlB7xn1KV9/v5iMhFi6BC7Mo6bRfCQ"
    "v9Sn0j3vU1vOsZ3i4U4oVxu/C2KuNYQuLVen0D4tV6fSVxrUsS54wUmtmh/f74AiHhdAr2"
    "g3iTOV1dPaWVKslXNWY85xBuMUYQpKu7OZ7zME8YI7viHL6695sCW4NBL7FZaXVHKbrj+1"
    "bn4aKioYsngv3yrNsfnfRx/HkLuZfz+NhKXLbP5TT9tALnu+8PiMAVvVQ53Xrl+CSeWEbx"
    "rwTbQ4p9kDixtbIS0i53e03EsTXL7Q31Nes7QyObo9nydakssONTmFNTJVg7x7v9cNQQfq"
    "5Wap9rXz7d1L5cGkAPcyn5vOY1G6av1Tu8Z8TDFbRpcRZzOde/m9W/alEV6bP1zUtIdyf7"
    "Z4tRifylvWmTbcxl/022hznh/fZR7bQH7VN4/xcmF7R9"
)
