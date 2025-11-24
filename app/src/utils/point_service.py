from app.src.models.point import CategoryCode, WalletKind, TxType
from app.src.router.point.crud import crud_category, crud_wallet, crud_transaction


async def reward_user_points(
    session,
    user_id: str,
    category: CategoryCode,
):
    """
    Generic function untuk memberikan poin kepada user berdasarkan CategoryCode.
    Mengupdate wallet credit + achievement dan membuat transaction log.
    """

    category_obj = await crud_category.get_by_code(
        session=session,
        code=category
    )
    if not category_obj:
        raise ValueError(f"Category '{category.value}' not found")

    amount = category_obj.default_points

    # Update wallet credit
    wallet_credit = await crud_wallet.update_balance(
        session=session,
        user_id=user_id,
        wallet_type=WalletKind.credit,
        amount=amount,
        tx_type=TxType.earn,
    )

    # Update wallet achievement
    wallet_achievement = await crud_wallet.update_balance(
        session=session,
        user_id=user_id,
        wallet_type=WalletKind.achievement,
        amount=amount,
        tx_type=TxType.earn,
    )

    # Create transaction for credit
    await crud_transaction.create(
        session=session,
        user_id=user_id,
        wallet=WalletKind.credit,
        tx_type=TxType.earn,
        category_code=category,
        delta=amount,
        balance_after=wallet_credit.credit_points,
    )

    # Create transaction for achievement
    await crud_transaction.create(
        session=session,
        user_id=user_id,
        wallet=WalletKind.achievement,
        tx_type=TxType.earn,
        category_code=category,
        delta=amount,
        balance_after=wallet_achievement.achievement_points,
    )

    return amount
