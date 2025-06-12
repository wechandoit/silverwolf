from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

db = SQLAlchemy()

class Player(db.Model):
    __tablename__ = "player"
    id: Mapped[int] = mapped_column(primary_key=True)
    puuid: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    tag: Mapped[str]
    region: Mapped[str]

class Verbose_Player(db.Model):
    __tablename__ = "verbose_player"
    id: Mapped[int] = mapped_column(primary_key=True)
    puuid: Mapped[str] = mapped_column(unique=True)
    account_level: Mapped[int] = mapped_column(default=0)
    card: Mapped[str]
    title: Mapped[str]

class MMR_History(db.Model):
    __tablename__ = "mmr_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[str]
    puuid: Mapped[str]
    mmr_change: Mapped[int]
    refunded_rr: Mapped[int]
    was_derank_protected: Mapped[int]
    map: Mapped[str]
    account_rank: Mapped[str]
    account_rr: Mapped[int]
    account_rank_img: Mapped[str]
    date: Mapped[int]

class Competitive_Match(db.Model):
    __tablename__ = "competitive_match"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[str] = mapped_column(unique=True)
    map: Mapped[str]
    game_length: Mapped[int]
    game_start: Mapped[int]
    region: Mapped[str]
    server: Mapped[str]
    blue_score: Mapped[int]
    red_score: Mapped[int]
    who_won: Mapped[str]
    match_players = relationship("Competitive_Match_Player", back_populates="match", cascade="all, delete-orphan")
    match_kills = relationship("Competitive_Match_Kill", back_populates="match", cascade="all, delete-orphan")

class Competitive_Match_Player(db.Model):
    __tablename__ = "competitive_match_player"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(db.ForeignKey("competitive_match.id"))
    puuid: Mapped[str]
    name: Mapped[str]
    tag: Mapped[str]
    agent: Mapped[str]
    party_id: Mapped[str]
    team: Mapped[str]
    score: Mapped[int]
    kills: Mapped[int]
    deaths: Mapped[int]
    assists: Mapped[int]
    headshots: Mapped[int]
    bodyshots: Mapped[int]
    legshots: Mapped[int]
    damage_dealt: Mapped[int]
    damage_received: Mapped[int]
    c_ability: Mapped[int]
    e_ability: Mapped[int]
    q_ability: Mapped[int]
    x_ability: Mapped[int]

    match = relationship("Competitive_Match", back_populates="match_players")

class Competitive_Match_Kill(db.Model):
    __tablename__ = "competitive_match_kills"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(db.ForeignKey("competitive_match.id"))
    time_in_round: Mapped[int]
    round: Mapped[int]
    killer_puuid: Mapped[str]
    victim_puuid: Mapped[str]
    killer_x: Mapped[int]
    killer_y: Mapped[int]
    victim_x: Mapped[int]
    victim_y: Mapped[int]
    killer_view: Mapped[float]
    weapon_id: Mapped[str]
    assistants: Mapped[List[str]] = mapped_column(ARRAY(String))

    match = relationship("Competitive_Match", back_populates="match_kills")