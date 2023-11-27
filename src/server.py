from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi import FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.responses import JSONResponse
from http import HTTPStatus
from typing import Optional

##Importei as bibliotecas de todas aulas :) 


from src.config.database import create_db_and_tables
from src.routes.reservas_routes import reservas_router
from src.routes.voos_routes import voos_router

@asynccontextmanager  #O que faz isso???

async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(voos_router)
app.include_router(reservas_router)


@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


@app.get("/voos/vendas")
def get_voos_vendas():
    limite_tempo = timedelta(hours=2)
    limite_tempo_partida = datetime.utcnow() + limite_tempo
    
    with Session(engine) as session:
        voos_vendas = (
            session.query(Voo)
            .filter(Voo.partida > datetime.utcnow(), Voo.partida <= limite_tempo_partida)
            .all()
        )
        
    return voos_vendas

@app.post("/voos", status_code=201)
def cria_voo(voos: voos_router):
    with Session(engine) as session:
        session.add(voos)
        session.commit(voos)
        session.refresh(voos)
        return voos
    
@app.post("/reservas")
def create_reserva(reservas_router):
    with Session(engine) as session:
        existe_reserva = (
            session.query(Reserva).filter(Reserva.documento == reservas_router["documento"]).first()
        )
    
    if existe_reserva:
        raise HTTPException(status_code=400, detail="Já temos uma reserva.")
    cria_reserva = cria_reserva(reserva_data)
    
    return cria_reserva

from fastapi import HTTPException

@app.post("/reserva/{codigo_reserva}/checkin/{num_poltrona}")
def create_checkin(codigo_reserva: str, num_poltrona: int):
    with Session(engine) as session:
        reserva = session.exec(select(Reserva).where(Reserva.codigo_reserva == codigo_reserva)).first()

        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")

        voo = session.exec(select(Voo).where(Voo.id == reserva.voo_id)).first()

        if not voo:
            raise HTTPException(status_code=500, detail="Voo não encontrado")

        if voo.is_poltrona_livre(num_poltrona):
            voo.marcar_poltrona(reserva, num_poltrona)
            session.commit()
            return {"message": f"Check-in realizado com sucesso para a poltrona {num_poltrona}"}
        else:
            raise HTTPException(status_code=403, detail="Poltrona ocupada")
@app.patch("/reserva/{codigo_reserva}/checkin/{num_poltrona}")
def update_checkin(codigo_reserva: str, num_poltrona: int):
    with Session(engine) as session:
        reserva = session.exec(select(Reserva).where(Reserva.codigo_reserva == codigo_reserva)).first()

        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")

        voo = session.exec(select(Voo).where(Voo.id == reserva.voo_id)).first()

        if not voo:
            raise HTTPException(status_code=500, detail="Voo não encontrado")

        if not voo.is_poltrona_livre(num_poltrona):
            raise HTTPException(status_code=403, detail="Poltrona ocupada")

        voo.marcar_poltrona(reserva, num_poltrona)
        session.commit()
        return {"message": f"Check-in realizado com sucesso para a poltrona {num_poltrona}"}

    

        
