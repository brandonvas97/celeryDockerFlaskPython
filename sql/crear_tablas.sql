DROP TABLE IF EXISTS procesos;

CREATE TABLE IF NOT EXISTS procesos (
  id SERIAL,
  fecha VARCHAR(50),
  numproceso VARCHAR(5000),
  accion VARCHAR(5000), 
  actores VARCHAR(5000), 
  procesados VARCHAR(5000), 
  cedulaactor VARCHAR(5000), 
  tipoaccion VARCHAR(5000), 
  tipojudicial VARCHAR(5000), 
  fechajudicial VARCHAR(5000)
);

CREATE TABLE usuarios(
  id SERIAL,
  usuario VARCHAR(200),
  contraseña VARCHAR(200)
);

INSERT INTO usuarios(usuario, contraseña) VALUES('bvasquez', '3132333435');