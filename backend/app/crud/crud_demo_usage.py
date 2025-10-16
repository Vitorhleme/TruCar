from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date
from app.models.demo_usage_model import DemoUsage
# CORREÇÃO: A importação agora é relativa ao diretório atual (crud)
from app.crud.base import CRUDBase

class CRUDDemoUsage(CRUDBase[DemoUsage, DemoUsage, DemoUsage]):
    async def get_or_create_usage(self, db: AsyncSession, *, organization_id: int, resource_type: str) -> DemoUsage:
        today = date.today()
        start_of_month = today.replace(day=1)

        stmt = select(DemoUsage).where(
            and_(
                DemoUsage.organization_id == organization_id,
                DemoUsage.resource_type == resource_type,
                DemoUsage.period == start_of_month
            )
        )
        result = await db.execute(stmt)
        usage = result.scalar_one_or_none()

        if not usage:
            usage = DemoUsage(
                organization_id=organization_id,
                resource_type=resource_type,
                period=start_of_month,
                usage_count=0
            )
            db.add(usage)
            await db.commit()
            await db.refresh(usage)
        return usage

    async def increment_usage(self, db: AsyncSession, *, organization_id: int, resource_type: str):
        usage = await self.get_or_create_usage(db, organization_id=organization_id, resource_type=resource_type)
        usage.usage_count += 1
        await db.commit()
        return usage

demo_usage = CRUDDemoUsage(DemoUsage)