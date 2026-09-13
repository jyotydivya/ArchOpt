"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-11 22:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='PROJECT_MANAGER'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    # 3. campus_requirements
    op.create_table(
        'campus_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('site_width', sa.Float(), nullable=False),
        sa.Column('site_height', sa.Float(), nullable=False),
        sa.Column('total_area', sa.Float(), nullable=True),
        sa.Column('min_green_percent', sa.Float(), nullable=False),
        sa.Column('min_parking_percent', sa.Float(), nullable=False),
        sa.Column('min_road_width', sa.Float(), nullable=False),
        sa.Column('min_building_gap', sa.Float(), nullable=False),
        sa.Column('entrance_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('road_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )
    op.create_index(op.f('ix_campus_requirements_id'), 'campus_requirements', ['id'], unique=False)

    # 4. buildings
    op.create_table(
        'buildings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('zone', sa.String(length=100), nullable=False),
        sa.Column('width', sa.Float(), nullable=False),
        sa.Column('depth', sa.Float(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('floor_count', sa.Integer(), nullable=False),
        sa.Column('required_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_buildings_id'), 'buildings', ['id'], unique=False)

    # 5. constraints
    op.create_table(
        'constraints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('constraint_type', sa.String(length=100), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('operator', sa.String(length=20), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_constraints_id'), 'constraints', ['id'], unique=False)

    # 6. layout_runs
    op.create_table(
        'layout_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('algorithm', sa.String(length=100), nullable=False),
        sa.Column('population_size', sa.Integer(), nullable=False),
        sa.Column('generation_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_layout_runs_id'), 'layout_runs', ['id'], unique=False)

    # 7. layouts
    op.create_table(
        'layouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('feasible', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('layout_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metrics_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['layout_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_layouts_id'), 'layouts', ['id'], unique=False)

    # 8. selected_plans
    op.create_table(
        'selected_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('layout_id', sa.Integer(), nullable=False),
        sa.Column('selected_by', sa.Integer(), nullable=True),
        sa.Column('selected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['layout_id'], ['layouts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_selected_plans_id'), 'selected_plans', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_selected_plans_id'), table_name='selected_plans')
    op.drop_table('selected_plans')
    op.drop_index(op.f('ix_layouts_id'), table_name='layouts')
    op.drop_table('layouts')
    op.drop_index(op.f('ix_layout_runs_id'), table_name='layout_runs')
    op.drop_table('layout_runs')
    op.drop_index(op.f('ix_constraints_id'), table_name='constraints')
    op.drop_table('constraints')
    op.drop_index(op.f('ix_buildings_id'), table_name='buildings')
    op.drop_table('buildings')
    op.drop_index(op.f('ix_campus_requirements_id'), table_name='campus_requirements')
    op.drop_table('campus_requirements')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
