-- SYNTHETIC fixtures only; never run against source tables with operational data.
CREATE TABLE public.estados (id bigint PRIMARY KEY, nombre_estado text);
CREATE TABLE public.paquetes_certi (id bigint PRIMARY KEY, codigo text, fk_estado bigint, cuidad text, created_at timestamp, updated_at timestamp, peso numeric, precio numeric);
CREATE TABLE public.paquetes_ordi (id bigint PRIMARY KEY, codigo text, fk_estado bigint, ciudad text, created_at timestamp, updated_at timestamp, peso numeric, precio numeric);
CREATE TABLE public.paquetes_ems (id bigint PRIMARY KEY, codigo text, estado_id bigint, origen text, ciudad text, created_at timestamp, updated_at timestamp, peso numeric, precio numeric);
CREATE TABLE public.paquetes_contrato (id bigint PRIMARY KEY, codigo text, estados_id bigint, origen text, destino text, created_at timestamp, updated_at timestamp, peso numeric, precio numeric);
CREATE TABLE public.paquetes_int (id bigint PRIMARY KEY, codigo text, estado_id bigint, origen text, destino text, created_at timestamp, updated_at timestamp, peso numeric, precio numeric);
CREATE TABLE public.sucursales (id bigint PRIMARY KEY, "codigoSucursal" integer, municipio text, departamento text, telefono text);
INSERT INTO public.estados VALUES (1, 'Registrado ficticio'), (2, 'Estado de prueba');
INSERT INTO public.paquetes_certi VALUES (1, 'DEMO-CERTI-001', 1, 'La Paz', '2026-10-01 10:00', '2026-10-02 12:00', 0.5, 25.00);
INSERT INTO public.paquetes_ordi VALUES (1, 'DEMO-ORDI-001', 2, 'Cochabamba', '2026-10-03 10:00', '2026-10-04 12:00', 0.1, 10.00);
INSERT INTO public.paquetes_ems VALUES (1, 'DEMO-EMS-001', 1, 'La Paz', 'Santa Cruz', '2026-10-05 10:00', '2026-10-06 12:00', 1.0, 45.00);
INSERT INTO public.paquetes_contrato VALUES (1, 'DEMO-CONTRATO-001', 1, 'Oruro', 'La Paz', '2026-10-07 10:00', '2026-10-08 12:00', 2.0, 80.00);
INSERT INTO public.paquetes_int VALUES (1, 'DEMO-INT-001', NULL, 'La Paz', 'Destino ficticio', '2026-10-09 10:00', '2026-10-10 12:00', 0.8, 50.00);
INSERT INTO public.sucursales VALUES (1, 999, 'La Paz', 'La Paz', '00000000');
