from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        INSERT INTO "shopsettings"
            (id, name, address, phone, receipt_header, receipt_footer, print_format, currency, language, theme)
        VALUES
            (1, 'Al-Karim electric service',
             'In front of Azhar clinic near muslim public high school peoples colony mumtaz abad multan',
             '03017458983 / 03346141413', '', '', 'a4', 'PKR', 'ur', 'light')
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            address = EXCLUDED.address,
            phone = EXCLUDED.phone;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    # Keep owner-provided business identity; edit it through Settings if needed.
    return ""


MODELS_STATE = (
    "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"
    "vZt/8DnCHuwA=="
)
