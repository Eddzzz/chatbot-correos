-- Structure only; no rows, functions, ownership or grants. Not a migration.

CREATE TABLE public.activity_logs (
    id bigint NOT NULL,
    user_id bigint,
    action character varying(255) NOT NULL,
    module character varying(100),
    details text,
    ip_address character varying(45),
    user_agent character varying(255),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    model character varying(120),
    record_id bigint,
    changes_json json,
    fecha timestamp(0) without time zone,
    vehicle_log_id bigint
);

CREATE TABLE public.alerta_empresa_destinatarios (
    alerta_empresa_id bigint NOT NULL,
    empresa_id bigint NOT NULL
);

CREATE TABLE public.alerta_empresa_lecturas (
    alerta_empresa_id bigint NOT NULL,
    user_id bigint NOT NULL,
    leida_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE public.alerta_empresa_usuarios (
    alerta_empresa_id bigint NOT NULL,
    user_id bigint NOT NULL
);

CREATE TABLE public.alertas_empresa (
    id bigint NOT NULL,
    titulo character varying(150) NOT NULL,
    mensaje text,
    portada_path character varying(255) NOT NULL,
    pdf_path character varying(255),
    creado_por bigint,
    publicada_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    vence_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    aprobada_at timestamp(0) without time zone,
    aprobada_por bigint
);

CREATE TABLE public.app_settings (
    id bigint NOT NULL,
    key character varying(255) NOT NULL,
    value text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.auditoria (
    id bigint NOT NULL,
    nombre_evento character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.bastion_carteros (
    id bigint NOT NULL,
    id_paquetes_ems bigint,
    id_paquetes_certi bigint,
    id_estados bigint NOT NULL,
    id_user bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    intento integer DEFAULT 0 NOT NULL,
    recibido_por character varying(255),
    descripcion text,
    id_paquetes_contrato bigint,
    foto character varying(255),
    imagen text,
    id_paquetes_ordi bigint,
    imagen_devolucion text,
    id_solicitud_cliente bigint,
    id_estado_anterior bigint
);

CREATE TABLE public.bastion_certi (
    codigo character varying(255),
    cod_especial character varying(255),
    servicio_id bigint,
    destinatario character varying(255),
    telefono integer,
    cuidad character varying(255),
    zona character varying(255),
    ventanilla character varying(255),
    peso numeric(10,3),
    precio numeric(10,2),
    tipo character varying(255),
    aduana character varying(255),
    observaciones text,
    fk_estado bigint,
    fk_ventanilla bigint,
    imagen text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    id_origen bigint,
    id bigint NOT NULL
);

CREATE TABLE public.bastion_contratos (
    user_id bigint,
    empresa_id bigint,
    codigo character varying(255),
    codigo_madre character varying(255),
    cod_especial character varying(50),
    estados_id bigint,
    origen character varying(255),
    provincia_origen character varying(255),
    destino character varying(255),
    nombre_r character varying(255),
    telefono_r character varying(255),
    contenido text,
    cantidad character varying(255),
    direccion_r character varying(255),
    nombre_d character varying(255),
    telefono_d character varying(255),
    direccion_d character varying(255),
    mapa character varying(255),
    provincia character varying(255),
    peso numeric(10,3),
    precio numeric(10,2),
    tarifa_contrato_id bigint,
    fecha_recojo timestamp(0) without time zone,
    observacion text,
    justificacion text,
    imagen text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    id_origen bigint,
    id bigint NOT NULL
);

CREATE TABLE public.bastion_ems (
    origen character varying(255),
    tipo_correspondencia character varying(255),
    servicio_especial character varying(255),
    contenido text,
    cantidad integer,
    peso numeric(10,3),
    codigo character varying(255),
    cod_especial character varying(20),
    precio numeric(10,2),
    nombre_remitente character varying(255),
    nombre_envia character varying(255),
    carnet character varying(255),
    telefono_remitente character varying(255),
    nombre_destinatario character varying(255),
    telefono_destinatario character varying(255),
    direccion character varying(255),
    referencia character varying(255),
    imagen text,
    observacion text,
    ciudad character varying(255),
    tarifario_id bigint,
    estado_id bigint,
    user_id bigint,
    justificacion text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    id_origen bigint,
    id bigint NOT NULL
);

CREATE TABLE public.bastion_ems_formulario (
    id bigint,
    paquete_ems_id bigint,
    origen character varying(255),
    tipo_correspondencia character varying(255),
    servicio_especial character varying(255),
    contenido text,
    cantidad integer,
    peso numeric(10,3),
    codigo character varying(255),
    precio numeric(10,2),
    nombre_remitente character varying(255),
    nombre_envia character varying(255),
    carnet character varying(255),
    telefono_remitente character varying(255),
    nombre_destinatario character varying(255),
    telefono_destinatario character varying(255),
    ciudad character varying(255),
    servicio_id bigint,
    destino_id bigint,
    tarifario_id bigint,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    direccion character varying(255),
    referencia character varying(255)
);

CREATE TABLE public.bastion_eventos (
    id bigint NOT NULL,
    tabla_origen character varying(40) NOT NULL,
    id_origen bigint NOT NULL,
    tipo_paquete character varying(20) NOT NULL,
    codigo character varying(255) NOT NULL,
    evento_id bigint NOT NULL,
    user_id bigint,
    cliente_id bigint,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.bastion_ordi (
    codigo character varying(255),
    servicio_id bigint,
    destinatario character varying(255),
    telefono character varying(30),
    ciudad character varying(255),
    zona character varying(255),
    peso numeric(10,3),
    precio numeric(10,2),
    aduana character varying(50),
    observaciones text,
    cod_especial character varying(255),
    fk_ventanilla bigint,
    fk_estado bigint,
    imagen text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    id_origen bigint,
    pais character varying(10),
    iso character varying(100),
    tipo character varying(50),
    factura character varying(100),
    manifiesto character varying(50),
    id bigint NOT NULL
);

CREATE TABLE public.bitacoras (
    id bigint NOT NULL,
    paquetes_ems_id bigint,
    paquetes_contrato_id bigint,
    user_id bigint NOT NULL,
    cod_especial character varying(50) NOT NULL,
    transportadora character varying(255),
    provincia character varying(255),
    factura character varying(255),
    precio_total numeric(10,2),
    peso numeric(10,3),
    imagen_factura character varying(255),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    paquetes_ordi_id bigint,
    paquetes_certi_id bigint,
    qr_url character varying(255),
    qr_texto text,
    qr_datos json,
    factura_fecha_emision timestamp(0) without time zone,
    factura_nit_emisor character varying(50),
    factura_cuf character varying(255),
    factura_razon_social character varying(255),
    factura_cliente character varying(255),
    factura_direccion character varying(255)
);

CREATE TABLE public.cache (
    key character varying(255) NOT NULL,
    value text NOT NULL,
    expiration integer NOT NULL
);

CREATE TABLE public.cache_locks (
    key character varying(255) NOT NULL,
    owner character varying(255) NOT NULL,
    expiration integer NOT NULL
);

CREATE TABLE public.cartero (
    id bigint NOT NULL,
    id_paquetes_ems bigint,
    id_paquetes_certi bigint,
    id_estados bigint NOT NULL,
    id_user bigint,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    intento integer DEFAULT 0 NOT NULL,
    recibido_por character varying(255),
    descripcion text,
    id_paquetes_contrato bigint,
    foto character varying(255),
    imagen text,
    id_paquetes_ordi bigint,
    imagen_devolucion text,
    id_solicitud_cliente bigint,
    id_estado_anterior bigint
);

CREATE TABLE public.cartero_assignment_report_items (
    id bigint NOT NULL,
    cartero_assignment_report_id bigint NOT NULL,
    tipo_paquete character varying(30) NOT NULL,
    paquete_id bigint NOT NULL,
    codigo character varying(255),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.cartero_assignment_reports (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    token uuid NOT NULL,
    assigned_user_id bigint,
    actor_user_id bigint,
    regional character varying(255),
    assigned_at timestamp(0) without time zone,
    total_assigned integer DEFAULT 0 NOT NULL,
    summary_by_type json,
    rows json,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.cartero_guias (
    id bigint NOT NULL,
    guia character varying(255) NOT NULL,
    transportadora character varying(255) NOT NULL,
    provincia character varying(255) NOT NULL,
    user_id bigint NOT NULL,
    factura character varying(255),
    codigo character varying(255) NOT NULL,
    precio_total numeric(10,2),
    peso_total numeric(10,3),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.cashier_flow_receivable_collections (
    id bigint NOT NULL,
    scope_hash character(64) NOT NULL,
    servicio character varying(180) NOT NULL,
    anio smallint NOT NULL,
    meses json NOT NULL,
    limite smallint DEFAULT '200'::smallint NOT NULL,
    departamento character varying(120),
    monto_cobrado numeric(16,2) NOT NULL,
    cobrado_por bigint,
    cobrado_at timestamp(0) without time zone NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    cobro_activo boolean DEFAULT true NOT NULL,
    devuelto_at timestamp(0) without time zone,
    devuelto_por bigint
);

CREATE TABLE public.cashier_flow_receivable_movements (
    id bigint NOT NULL,
    movement_key character(64) NOT NULL,
    servicio character varying(180) NOT NULL,
    anio smallint NOT NULL,
    mes smallint NOT NULL,
    venta_id character varying(180),
    detalle_id character varying(180),
    codigo_orden character varying(180),
    codigo_seguimiento character varying(180),
    fecha character varying(80),
    descripcion text,
    monto numeric(16,2) NOT NULL,
    cobro_activo boolean DEFAULT true NOT NULL,
    cobrado_por bigint,
    cobrado_at timestamp(0) without time zone NOT NULL,
    devuelto_por bigint,
    devuelto_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    facturado_por_id character varying(80),
    facturado_por_nombre character varying(180),
    facturado_por_email character varying(180),
    facturado_por_alias character varying(180),
    cantidad_paquetes numeric(16,2) DEFAULT '0'::numeric NOT NULL
);

CREATE TABLE public.chasqui_location_points (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    location_id character varying(64) NOT NULL,
    device_id character varying(190) NOT NULL,
    device_name character varying(120),
    latitude numeric(10,7) NOT NULL,
    longitude numeric(10,7) NOT NULL,
    accuracy_m numeric(10,2),
    speed_kmh numeric(8,2),
    heading numeric(6,2),
    battery_percent numeric(5,2),
    is_moving boolean DEFAULT false NOT NULL,
    gps_enabled boolean DEFAULT true NOT NULL,
    gps_mocked boolean DEFAULT false NOT NULL,
    sent_at timestamp(0) without time zone NOT NULL,
    received_at timestamp(0) without time zone NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    is_simulated boolean DEFAULT false NOT NULL,
    route_label character varying(160)
);

CREATE TABLE public.clientes (
    id integer NOT NULL,
    user_id bigint,
    provider character varying(255) DEFAULT 'local'::character varying NOT NULL,
    google_id character varying(255) DEFAULT NULL::character varying,
    name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    avatar text,
    email_verified_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    password character varying(255) DEFAULT NULL::character varying,
    rol character varying(255) DEFAULT 'tiktokero'::character varying NOT NULL,
    remember_token character varying(100) DEFAULT NULL::character varying,
    codigo_cliente character varying(9) DEFAULT NULL::character varying,
    tipodocumentoidentidad character varying(50) DEFAULT NULL::character varying,
    numero_carnet character varying(50) DEFAULT NULL::character varying,
    razon_social character varying(255) DEFAULT NULL::character varying,
    telefono character varying(50) DEFAULT NULL::character varying,
    direccion character varying(255) DEFAULT NULL::character varying,
    complemento character varying(50) DEFAULT NULL::character varying
);

CREATE TABLE public.codigo_empresa (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    barcode character varying(255) NOT NULL,
    empresa_id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.conceptos_facturacion (
    id bigint NOT NULL,
    nombre character varying(255) NOT NULL,
    actividad_economica character varying(6) NOT NULL,
    codigo_sin character varying(7) NOT NULL,
    codigo character varying(50) NOT NULL,
    unidad_medida integer DEFAULT 58 NOT NULL,
    descripcion character varying(500) NOT NULL,
    precio_base numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.conciliaciones_empresa (
    id bigint NOT NULL,
    empresa_id bigint NOT NULL,
    anio smallint NOT NULL,
    mes smallint NOT NULL,
    gestora_at timestamp(0) without time zone,
    gestora_por bigint,
    conciliacion_at timestamp(0) without time zone,
    conciliacion_por bigint,
    documento_path character varying(255),
    documento_nombre character varying(255),
    documento_mime character varying(120),
    documento_tamano bigint,
    documento_at timestamp(0) without time zone,
    documento_por bigint,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    factura_venta_id character varying(100),
    factura_detalle_id character varying(100),
    factura_descripcion text,
    factura_codigo_orden character varying(100),
    factura_codigo_seguimiento character varying(100),
    factura_fecha timestamp(0) without time zone,
    factura_monto numeric(15,2),
    facturado_anio smallint,
    facturado_mes smallint,
    por_cobrar_at timestamp(0) without time zone,
    por_cobrar_por bigint,
    factura_cuf character varying(255),
    factura_numero character varying(100),
    factura_pdf_path character varying(255),
    factura_razon_social character varying(255),
    factura_codigo_cliente character varying(100),
    factura_numero_documento character varying(100),
    factura_tipo_documento character varying(30),
    pago_recibido_at timestamp(0) without time zone,
    pago_recibido_por bigint,
    pago_comprobante_path character varying(255),
    pago_comprobante_nombre character varying(255),
    pago_comprobante_tamano bigint,
    confirmacion_pago_at timestamp(0) without time zone,
    confirmacion_pago_por bigint,
    conciliado_at timestamp(0) without time zone,
    conciliado_por bigint,
    formato_nota_cobranza character varying(255),
    nombre_empresa_cobranza character varying(255)
);

CREATE TABLE public.correlativos_contrato (
    codigo_cliente character varying(255) NOT NULL,
    ultimo_correlativo bigint DEFAULT '0'::bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.despacho (
    id bigint NOT NULL,
    oforigen character varying(255) NOT NULL,
    ofdestino character varying(255) NOT NULL,
    categoria character varying(255) NOT NULL,
    subclase character varying(255) NOT NULL,
    nro_despacho character varying(255) NOT NULL,
    nro_envase character varying(255),
    peso numeric(10,3),
    identificador character varying(255),
    anio smallint NOT NULL,
    departamento character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    fk_estado bigint
);

CREATE TABLE public.destino (
    id bigint NOT NULL,
    nombre_destino character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.driver_incentive_reports (
    id bigint NOT NULL,
    driver_id bigint NOT NULL,
    report_year smallint NOT NULL,
    report_month smallint NOT NULL,
    stars_start smallint DEFAULT '5'::smallint NOT NULL,
    stars_end smallint DEFAULT '5'::smallint NOT NULL,
    non_preventive_requests integer DEFAULT 0 NOT NULL,
    preventive_requests integer DEFAULT 0 NOT NULL,
    generated_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    discountable_events integer DEFAULT 0 NOT NULL
);

CREATE TABLE public.drivers (
    id bigint NOT NULL,
    user_id bigint,
    nombre character varying(255) NOT NULL,
    licencia character varying(50),
    tipo_licencia character varying(20),
    fecha_vencimiento_licencia date,
    telefono character varying(20),
    email character varying(255),
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    memorandum_path character varying(255)
);

CREATE TABLE public.empresa (
    id bigint NOT NULL,
    nombre character varying(255) NOT NULL,
    sigla character varying(255) NOT NULL,
    codigo_cliente character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    clasificacion character varying(255),
    documentacion_legal character varying(255),
    inicio_contrato date,
    fin_contrato date,
    cobertura character varying(255),
    presupuesto numeric(14,2),
    documento_pdf_path character varying(255),
    nit character varying(32)
);

CREATE TABLE public.empresa_historiales (
    id bigint NOT NULL,
    empresa_id bigint,
    archivado_por bigint,
    nombre character varying(255) NOT NULL,
    sigla character varying(255),
    codigo_cliente character varying(255),
    clasificacion character varying(255),
    documentacion_legal character varying(255),
    inicio_contrato date,
    fin_contrato date,
    cobertura character varying(255),
    presupuesto numeric(15,2),
    documento_pdf_path character varying(255),
    datos_completos json NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    nit character varying(32)
);

CREATE TABLE public.entregas (
    id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.estados (
    id bigint NOT NULL,
    nombre_estado character varying(255) NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.eventos (
    id bigint NOT NULL,
    nombre_evento character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.eventos_auditoria (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    auditoria_id bigint NOT NULL,
    user_id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.eventos_certi (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    evento_id bigint NOT NULL,
    user_id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    codigo_relacionado character varying(255),
    detalle_evento text
);

CREATE TABLE public.eventos_contrato (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    evento_id bigint NOT NULL,
    user_id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    codigo_relacionado character varying(255),
    detalle_evento text
);

CREATE TABLE public.eventos_despacho (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    evento_id bigint NOT NULL,
    user_id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.eventos_ems (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    evento_id bigint NOT NULL,
    user_id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    codigo_relacionado character varying(255),
    detalle_evento text
);

CREATE TABLE public.eventos_ordi (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    evento_id bigint NOT NULL,
    user_id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    codigo_relacionado character varying(255),
    detalle_evento text
);

CREATE TABLE public.eventos_tiktoker (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    evento_id bigint NOT NULL,
    user_id bigint,
    cliente_id bigint,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    detalle_evento text
);

CREATE TABLE public.external_api_tokens (
    id bigint NOT NULL,
    user_id bigint,
    name character varying(255) NOT NULL,
    jti character varying(64) NOT NULL,
    token_hash character varying(64) NOT NULL,
    abilities json,
    is_active boolean DEFAULT true NOT NULL,
    last_used_at timestamp(0) without time zone,
    expires_at timestamp(0) without time zone,
    revoked_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    token_encrypted text,
    token_plain text
);

CREATE TABLE public.factura_ticket_snapshots (
    id bigint NOT NULL,
    cart_id bigint NOT NULL,
    data json NOT NULL,
    captured_at timestamp(0) without time zone NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.facturacion_clientes_frecuentes (
    id bigint NOT NULL,
    tipo_documento character varying(20) NOT NULL,
    numero_documento character varying(80) NOT NULL,
    complemento_documento character varying(30) DEFAULT ''::character varying NOT NULL,
    razon_social character varying(255) NOT NULL,
    correo_facturacion character varying(50),
    ultima_venta_id bigint,
    usos integer DEFAULT 1 NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.facturas (
    id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.failed_jobs (
    id bigint NOT NULL,
    uuid character varying(255) NOT NULL,
    connection text NOT NULL,
    queue text NOT NULL,
    payload text NOT NULL,
    exception text NOT NULL,
    failed_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE public.fuel_antifraud_cases (
    id bigint NOT NULL,
    case_key character varying(255) NOT NULL,
    type character varying(60) DEFAULT 'duplicate_invoice'::character varying NOT NULL,
    status character varying(40) DEFAULT 'pending'::character varying NOT NULL,
    invoice_number character varying(255),
    fuel_invoice_id bigint,
    conflicting_fuel_invoice_id bigint,
    fuel_log_id bigint,
    conflicting_fuel_log_id bigint,
    vehicle_id bigint,
    driver_id bigint,
    conflicting_vehicle_id bigint,
    conflicting_driver_id bigint,
    detected_source character varying(40),
    summary text,
    evidence_json json,
    reviewed_at timestamp(0) without time zone,
    reviewed_by_user_id bigint,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.fuel_invoice_details (
    id bigint NOT NULL,
    fuel_invoice_id bigint NOT NULL,
    fuel_log_id bigint,
    monto numeric(10,2),
    detalle text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    gas_station_id bigint,
    cantidad numeric(10,2),
    precio_unitario numeric(10,2),
    subtotal numeric(10,2),
    estado character varying(30) DEFAULT 'Falta verificar'::character varying NOT NULL,
    activo boolean DEFAULT true NOT NULL
);

CREATE TABLE public.fuel_invoices (
    id bigint NOT NULL,
    numero character varying(255) NOT NULL,
    fecha_emision date,
    gas_station_id bigint,
    monto_total numeric(10,2),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    numero_factura character varying(255),
    nombre_cliente character varying(255),
    siat_source_url character varying(255),
    siat_snapshot_json json,
    siat_document_path character varying(255),
    invoice_photo_path character varying(255),
    siat_rollo_document_path character varying(255),
    fuel_latitude numeric(10,7),
    fuel_longitude numeric(10,7),
    fuel_location_label character varying(255),
    fuel_recorded_at timestamp(0) without time zone,
    antifraud_payload_json json,
    activo boolean DEFAULT true NOT NULL
);

CREATE TABLE public.fuel_logs (
    id bigint NOT NULL,
    fecha timestamp(0) without time zone NOT NULL,
    galones numeric(10,2),
    precio_galon numeric(10,2),
    total_calculado numeric(10,2),
    kilometraje numeric(10,2),
    recibo character varying(255),
    observaciones text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone
);

CREATE TABLE public.gas_stations (
    id bigint NOT NULL,
    nombre character varying(255) DEFAULT 'SIN NOMBRE'::character varying NOT NULL,
    ubicacion character varying(255),
    ciudad character varying(255),
    provincia character varying(255),
    telefono character varying(20),
    email character varying(255),
    latitud numeric(10,8),
    longitud numeric(11,8),
    activa boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    nit_emisor character varying(50),
    razon_social character varying(255),
    direccion character varying(255)
);

CREATE TABLE public.job_batches (
    id character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    total_jobs integer NOT NULL,
    pending_jobs integer NOT NULL,
    failed_jobs integer NOT NULL,
    failed_job_ids text NOT NULL,
    options text,
    cancelled_at integer,
    created_at integer NOT NULL,
    finished_at integer
);

CREATE TABLE public.jobs (
    id bigint NOT NULL,
    queue character varying(255) NOT NULL,
    payload text NOT NULL,
    attempts smallint NOT NULL,
    reserved_at integer,
    available_at integer NOT NULL,
    created_at integer NOT NULL
);

CREATE TABLE public.jornadas_bitacoras (
    id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.maintenance_alert_user_reads (
    id bigint NOT NULL,
    maintenance_alert_id bigint NOT NULL,
    user_id bigint NOT NULL,
    read_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.maintenance_alerts (
    id bigint NOT NULL,
    vehicle_id bigint NOT NULL,
    maintenance_type_id bigint,
    maintenance_appointment_id bigint,
    tipo character varying(30) NOT NULL,
    mensaje character varying(255) NOT NULL,
    leida boolean DEFAULT false NOT NULL,
    status character varying(20) DEFAULT 'Activa'::character varying NOT NULL,
    fecha_resolucion timestamp(0) without time zone,
    usuario_id bigint,
    kilometraje_actual numeric(10,2),
    kilometraje_objetivo numeric(10,2),
    faltante_km numeric(10,2),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    postponed_until timestamp(0) without time zone,
    postponed_once boolean DEFAULT false NOT NULL
);

CREATE TABLE public.maintenance_appointments (
    id bigint NOT NULL,
    vehicle_id bigint,
    driver_id bigint,
    tipo_mantenimiento_id bigint,
    fecha_programada timestamp(0) without time zone,
    es_accidente boolean DEFAULT false NOT NULL,
    estado character varying(50) DEFAULT 'Pendiente'::character varying NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    approved_at timestamp(0) without time zone,
    approved_by_user_id bigint,
    requested_by_user_id bigint,
    solicitud_fecha timestamp(0) without time zone,
    origen_solicitud character varying(40) DEFAULT 'web'::character varying NOT NULL,
    evidencia_path character varying(255),
    formulario_documento_path character varying(255),
    activo boolean DEFAULT true NOT NULL
);

CREATE TABLE public.maintenance_logs (
    id bigint NOT NULL,
    vehicle_id bigint NOT NULL,
    tipo character varying(100),
    fecha date,
    proxima_fecha date,
    costo numeric(10,2),
    kilometraje numeric(10,2),
    taller character varying(255),
    descripcion text,
    comprobante character varying(255),
    observaciones text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    maintenance_type_id bigint,
    proximo_kilometraje numeric(10,2),
    activo boolean DEFAULT true NOT NULL
);

CREATE TABLE public.maintenance_type_vehicle (
    id bigint NOT NULL,
    maintenance_type_id bigint NOT NULL,
    vehicle_id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.maintenance_types (
    id bigint NOT NULL,
    vehicle_class_id bigint,
    nombre character varying(255) NOT NULL,
    cada_km integer,
    intervalo_km integer,
    intervalo_km_init integer,
    intervalo_km_fh integer,
    km_alerta_previa integer DEFAULT 15 NOT NULL,
    descripcion text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    es_preventivo boolean DEFAULT false NOT NULL,
    maintenance_form_type character varying(20),
    activo boolean DEFAULT true NOT NULL,
    categoria character varying(40) DEFAULT 'preventivo_km'::character varying NOT NULL
);

CREATE TABLE public.malencaminados (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    observacion text,
    malencaminamiento integer DEFAULT 1 NOT NULL,
    paquetes_ems_id bigint,
    paquetes_contrato_id bigint,
    destino_anterior character varying(255),
    destino_nuevo character varying(255),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    departamento_origen character varying(50),
    paquetes_certi_id bigint,
    paquetes_ordi_id bigint,
    user_id bigint
);

CREATE TABLE public.migrations (
    id integer NOT NULL,
    migration character varying(255) NOT NULL,
    batch integer NOT NULL
);

CREATE TABLE public.mobile_db_snapshots (
    id bigint NOT NULL,
    user_id bigint,
    snapshot_key character varying(120) NOT NULL,
    sent_at timestamp(0) without time zone,
    action character varying(120) NOT NULL,
    model character varying(190) NOT NULL,
    table_name character varying(120),
    record_id bigint,
    page integer,
    total_pages integer,
    payload_json text,
    payload_size integer DEFAULT 0 NOT NULL,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.model_has_permissions (
    permission_id bigint NOT NULL,
    model_type character varying(255) NOT NULL,
    model_id bigint NOT NULL
);

CREATE TABLE public.model_has_roles (
    role_id bigint NOT NULL,
    model_type character varying(255) NOT NULL,
    model_id bigint NOT NULL
);

CREATE TABLE public.origen (
    id bigint NOT NULL,
    nombre_origen character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.paquetes_certi (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    destinatario character varying(255) NOT NULL,
    telefono integer,
    cuidad character varying(255) NOT NULL,
    zona character varying(255),
    ventanilla character varying(255) NOT NULL,
    peso numeric(10,3) NOT NULL,
    tipo character varying(255) NOT NULL,
    aduana character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    fk_estado bigint NOT NULL,
    fk_ventanilla bigint NOT NULL,
    cod_especial character varying,
    imagen text,
    precio numeric(10,2),
    servicio_id bigint,
    observaciones text
);

CREATE TABLE public.paquetes_contrato (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    origen character varying(255) NOT NULL,
    destino character varying(255) NOT NULL,
    nombre_r character varying(255) NOT NULL,
    telefono_r character varying(255) NOT NULL,
    contenido text NOT NULL,
    direccion_r character varying(255) NOT NULL,
    nombre_d character varying(255) NOT NULL,
    telefono_d character varying(255),
    direccion_d character varying(255) NOT NULL,
    mapa character varying(255),
    provincia character varying(255),
    peso numeric(10,3) NOT NULL,
    fecha_recojo timestamp(0) without time zone,
    observacion text,
    justificacion text,
    imagen text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    estados_id bigint,
    cod_especial character varying(50),
    empresa_id bigint,
    precio numeric(10,2),
    tarifa_contrato_id bigint,
    cantidad character varying(255),
    codigo_madre character varying(255),
    provincia_origen character varying(255),
    destino_registrado character varying(255),
    envio_cn33 timestamp(0) without time zone
);

CREATE TABLE public.paquetes_ems (
    id bigint NOT NULL,
    origen character varying(255),
    tipo_correspondencia character varying(255),
    contenido text,
    cantidad integer,
    peso numeric(10,3),
    codigo character varying(255),
    precio numeric(10,2),
    nombre_remitente character varying(255),
    nombre_envia character varying(255),
    carnet character varying(255),
    telefono_remitente character varying(255),
    nombre_destinatario character varying(255),
    telefono_destinatario character varying(255),
    ciudad character varying(255),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    user_id bigint,
    tarifario_id bigint,
    servicio_especial character varying(255),
    estado_id bigint,
    cod_especial character varying(20),
    direccion character varying(255),
    imagen text,
    referencia character varying(255),
    observacion text,
    justificacion text,
    envio_cn33 timestamp(0) without time zone,
    correo_electronico character varying(255)
);

CREATE TABLE public.paquetes_ems_formulario (
    id bigint NOT NULL,
    paquete_ems_id bigint NOT NULL,
    origen character varying(255),
    tipo_correspondencia character varying(255) NOT NULL,
    servicio_especial character varying(255),
    contenido text NOT NULL,
    cantidad integer NOT NULL,
    peso numeric(10,3) NOT NULL,
    codigo character varying(255),
    precio numeric(10,2),
    nombre_remitente character varying(255) NOT NULL,
    nombre_envia character varying(255) NOT NULL,
    carnet character varying(255) NOT NULL,
    telefono_remitente character varying(255) NOT NULL,
    nombre_destinatario character varying(255) NOT NULL,
    telefono_destinatario character varying(255) NOT NULL,
    ciudad character varying(255),
    servicio_id bigint,
    destino_id bigint,
    tarifario_id bigint,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    direccion character varying(255),
    referencia character varying(255),
    correo_electronico character varying(255)
);

CREATE TABLE public.paquetes_int (
    id bigint NOT NULL,
    cod_especial character varying(50),
    codigo character varying(100) NOT NULL,
    peso numeric(10,3) NOT NULL,
    destino character varying(120),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    origen character varying(120),
    precio numeric(10,2),
    enviado_admision_at timestamp(0) without time zone,
    servicio_id bigint,
    estado_id bigint,
    tramo character varying(120),
    envio_cn33 timestamp(0) without time zone
);

CREATE TABLE public.paquetes_ordi (
    id bigint NOT NULL,
    codigo character varying(255) NOT NULL,
    destinatario character varying(255) NOT NULL,
    telefono character varying(30) NOT NULL,
    ciudad character varying(255) NOT NULL,
    zona character varying(255) NOT NULL,
    peso numeric(10,3) NOT NULL,
    aduana character varying(50) NOT NULL,
    observaciones text,
    cod_especial character varying(255),
    fk_ventanilla bigint NOT NULL,
    fk_estado bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    imagen text,
    pais character varying(10),
    iso character varying(100),
    tipo character varying(50),
    precio numeric(10,2),
    factura character varying(100),
    manifiesto character varying(50),
    servicio_id bigint
);

CREATE TABLE public.password_reset_tokens (
    email character varying(255) NOT NULL,
    token character varying(255) NOT NULL,
    created_at timestamp(0) without time zone
);

CREATE TABLE public.permissions (
    id bigint NOT NULL,
    name character varying(255) NOT NULL,
    guard_name character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.personal_access_tokens (
    id bigint NOT NULL,
    tokenable_type character varying(255) NOT NULL,
    tokenable_id bigint NOT NULL,
    name text NOT NULL,
    token character varying(64) NOT NULL,
    abilities text,
    last_used_at timestamp(0) without time zone,
    expires_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.peso (
    id bigint NOT NULL,
    peso_inicial numeric(10,3) NOT NULL,
    peso_final numeric(10,3) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.plantillas (
    id bigint NOT NULL,
    nombre character varying(255) NOT NULL,
    ciudad character varying(255) NOT NULL,
    destinatario character varying(255) NOT NULL,
    remitente character varying(255) NOT NULL,
    telefono character varying(255) NOT NULL,
    ciudad_destino character varying(255) NOT NULL,
    estado character varying(255) DEFAULT 'LISTO'::character varying NOT NULL,
    observacion text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.preregistros (
    id bigint NOT NULL,
    estado character varying(30) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    origen character varying(255) NOT NULL,
    tipo_correspondencia character varying(255),
    servicio_especial character varying(255),
    contenido text NOT NULL,
    cantidad integer NOT NULL,
    peso numeric(10,3),
    precio numeric(10,2),
    nombre_remitente character varying(255) NOT NULL,
    nombre_envia character varying(255),
    carnet character varying(255) NOT NULL,
    telefono_remitente character varying(255),
    nombre_destinatario character varying(255) NOT NULL,
    telefono_destinatario character varying(255),
    direccion character varying(255) NOT NULL,
    ciudad character varying(255) NOT NULL,
    servicio_id bigint,
    destino_id bigint NOT NULL,
    validado_por bigint,
    validado_at timestamp(0) without time zone,
    paquete_ems_id bigint,
    codigo_generado character varying(255),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    codigo_preregistro character varying(20),
    correo_electronico character varying(255),
    referencia character varying(255),
    observacion text
);

CREATE TABLE public.pulse_aggregates (
    id bigint NOT NULL,
    bucket integer NOT NULL,
    period integer NOT NULL,
    type character varying(255) NOT NULL,
    key text NOT NULL,
    key_hash uuid GENERATED ALWAYS AS ((md5(key))::uuid) STORED NOT NULL,
    aggregate character varying(255) NOT NULL,
    value numeric(20,2) NOT NULL,
    count integer
);

CREATE TABLE public.pulse_entries (
    id bigint NOT NULL,
    "timestamp" integer NOT NULL,
    type character varying(255) NOT NULL,
    key text NOT NULL,
    key_hash uuid GENERATED ALWAYS AS ((md5(key))::uuid) STORED NOT NULL,
    value bigint
);

CREATE TABLE public.pulse_values (
    id bigint NOT NULL,
    "timestamp" integer NOT NULL,
    type character varying(255) NOT NULL,
    key text NOT NULL,
    key_hash uuid GENERATED ALWAYS AS ((md5(key))::uuid) STORED NOT NULL,
    value text NOT NULL
);

CREATE TABLE public.recorridos (
    id bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.remitentes_ems (
    id bigint NOT NULL,
    nombre_remitente character varying(255) NOT NULL,
    telefono_remitente character varying(50) NOT NULL,
    carnet character varying(100) NOT NULL,
    nombre_envia character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.role_has_permissions (
    permission_id bigint NOT NULL,
    role_id bigint NOT NULL
);

CREATE TABLE public.roles (
    id bigint NOT NULL,
    name character varying(255) NOT NULL,
    guard_name character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    nombre character varying(255)
);

CREATE TABLE public.saca (
    id bigint NOT NULL,
    nro_saca character varying(255) NOT NULL,
    identificador character varying(255) NOT NULL,
    peso numeric(10,3),
    paquetes integer,
    busqueda character varying(255),
    receptaculo character varying(255),
    fk_despacho bigint NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    fk_estado bigint
);

CREATE TABLE public.servicio (
    id bigint NOT NULL,
    nombre_servicio character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    "actividadEconomica" character varying(6),
    "codigoSin" character varying(7),
    codigo character varying(50),
    descripcion character varying(500),
    "unidadMedida" integer
);

CREATE TABLE public.servicio_extras (
    id integer NOT NULL,
    nombre character varying(255) NOT NULL,
    descripcion character varying(255) DEFAULT NULL::character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE TABLE public.sessions (
    id character varying(255) NOT NULL,
    user_id bigint,
    ip_address character varying(45),
    user_agent text,
    payload text NOT NULL,
    last_activity integer NOT NULL
);

CREATE TABLE public.solicitud_clientes (
    id integer NOT NULL,
    cliente_id bigint,
    codigo_solicitud character varying(255) DEFAULT NULL::character varying,
    origen character varying(255) NOT NULL,
    tipo_correspondencia character varying(255) DEFAULT NULL::character varying,
    servicio_especial character varying(255) DEFAULT NULL::character varying,
    contenido text NOT NULL,
    cantidad integer NOT NULL,
    peso numeric(10,3) DEFAULT NULL::numeric,
    precio numeric(10,2) DEFAULT NULL::numeric,
    nombre_remitente character varying(255) NOT NULL,
    nombre_envia character varying(255) DEFAULT NULL::character varying,
    carnet character varying(255) NOT NULL,
    telefono_remitente character varying(255) DEFAULT NULL::character varying,
    nombre_destinatario character varying(255) NOT NULL,
    telefono_destinatario character varying(255) DEFAULT NULL::character varying,
    direccion character varying(255) NOT NULL,
    ciudad character varying(255) NOT NULL,
    servicio_id bigint,
    destino_id bigint NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    tarifario_tiktoker_id bigint,
    servicio_extra_id bigint,
    direccion_recojo character varying(255) DEFAULT NULL::character varying,
    barcode character varying(255) DEFAULT NULL::character varying,
    estado_id bigint,
    pago_destinatario boolean DEFAULT false NOT NULL,
    cod_especial character varying(255) DEFAULT NULL::character varying,
    recepcionado_por character varying(255) DEFAULT NULL::character varying,
    observacion text,
    imagen text,
    justificacion text,
    envio_cn33 timestamp(0) without time zone,
    paquete_muy_grande boolean DEFAULT false NOT NULL
);

CREATE TABLE public.subscriptions (
    id bigint NOT NULL,
    codigo character varying(64) NOT NULL,
    fcm_token character varying(512) NOT NULL,
    package_name character varying(256),
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.sucursales (
    id bigint NOT NULL,
    "codigoSucursal" integer NOT NULL,
    "puntoVenta" integer NOT NULL,
    municipio character varying(25) NOT NULL,
    departamento character varying(15),
    telefono character varying(8) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.system_audit_logs (
    id bigint NOT NULL,
    occurred_at timestamp(0) with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    table_name character varying(190) NOT NULL,
    operation character varying(12) NOT NULL,
    record_identifier text,
    request_user_id bigint,
    request_user_name text,
    request_user_alias text,
    request_ip character varying(45),
    user_agent text,
    database_user character varying(190),
    database_session_user character varying(190),
    database_client_ip character varying(64),
    application_name text,
    database_pid integer,
    changed_fields jsonb NOT NULL,
    old_values jsonb,
    new_values jsonb
);

CREATE TABLE public.tarifa_contrato (
    id bigint NOT NULL,
    empresa_id bigint NOT NULL,
    origen character varying(255) NOT NULL,
    destino character varying(255) NOT NULL,
    servicio character varying(255) NOT NULL,
    kilo numeric(10,2) NOT NULL,
    kilo_extra numeric(10,2) NOT NULL,
    provincia character varying(255),
    retencion numeric(10,2) NOT NULL,
    horas_entrega integer NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    direccion character varying(255),
    zona character varying(255),
    peso numeric(10,2),
    provincia_origen character varying(255)
);

CREATE TABLE public.tarifario (
    id bigint NOT NULL,
    servicio_id bigint,
    destino_id bigint,
    peso_id bigint,
    origen_id bigint,
    precio numeric(10,2),
    observacion text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.tarifario_tiktoker (
    id integer NOT NULL,
    origen_id bigint NOT NULL,
    destino_id bigint NOT NULL,
    peso1 numeric(10,2) NOT NULL,
    peso2 numeric(10,2),
    peso3 numeric(10,2),
    peso_extra numeric(10,2),
    tiempo_entrega integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    servicio_extra_id bigint
);

CREATE TABLE public.telescope_entries (
    sequence bigint NOT NULL,
    uuid uuid NOT NULL,
    batch_id uuid NOT NULL,
    family_hash character varying(255),
    should_display_on_index boolean DEFAULT true NOT NULL,
    type character varying(20) NOT NULL,
    content text NOT NULL,
    created_at timestamp(0) without time zone
);

CREATE TABLE public.telescope_entries_tags (
    entry_uuid uuid NOT NULL,
    tag character varying(255) NOT NULL
);

CREATE TABLE public.telescope_monitoring (
    tag character varying(255) NOT NULL
);

CREATE TABLE public.tracking_local_event_rules (
    id bigint NOT NULL,
    source_table character varying(80) DEFAULT '*'::character varying NOT NULL,
    event_id bigint,
    raw_name character varying(255) DEFAULT ''::character varying NOT NULL,
    display_name character varying(255),
    is_visible boolean DEFAULT true NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    notes text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.tracking_subscriptions (
    id bigint NOT NULL,
    codigo character(13) NOT NULL,
    fcm_token text NOT NULL,
    package_name character varying(120),
    last_sig text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);

CREATE TABLE public.user_ips_links (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    ips_user_pid smallint NOT NULL,
    ips_user_domain character varying(20) DEFAULT ''::character varying NOT NULL,
    ips_user_fid character varying(255) NOT NULL,
    ips_user_name character varying(255) NOT NULL,
    ips_office_cd smallint,
    ips_office_fcd character varying(25),
    ips_office_name character varying(64),
    ipsweb boolean DEFAULT false NOT NULL,
    restrict_user_offices boolean DEFAULT false NOT NULL,
    active boolean DEFAULT true NOT NULL,
    last_verified_at timestamp(0) without time zone,
    last_snapshot json,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.user_login_logs (
    id bigint NOT NULL,
    user_id bigint,
    user_name character varying(255),
    user_alias character varying(255),
    ip_address character varying(45),
    user_agent text,
    session_id character varying(255),
    logged_in_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    logged_out_at timestamp(0) without time zone
);

CREATE TABLE public.users (
    id bigint NOT NULL,
    name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    email_verified_at timestamp(0) without time zone,
    password character varying(255) NOT NULL,
    ciudad character varying(255),
    ci character varying(255),
    remember_token character varying(100),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    empresa_id bigint,
    alias character varying(255),
    role_id bigint,
    sucursal_id bigint,
    regionales json,
    auto_baja_empresa_at timestamp(0) without time zone,
    provincia_origen character varying(255)
);

CREATE TABLE public.vehicle_assignments (
    id bigint NOT NULL,
    driver_id bigint,
    vehicle_id bigint,
    tipo_asignacion character varying(100),
    fecha_inicio timestamp(0) without time zone,
    fecha_fin timestamp(0) without time zone,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.vehicle_brands (
    id bigint NOT NULL,
    nombre character varying(255) NOT NULL,
    pais_origen character varying(255),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    activo boolean DEFAULT true NOT NULL
);

CREATE TABLE public.vehicle_classes (
    id bigint NOT NULL,
    marca_id bigint,
    modelo character varying(50) NOT NULL,
    anio integer NOT NULL,
    nombre character varying(180) NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    maintenance_form_type character varying(20)
);

CREATE TABLE public.vehicle_log (
    id bigint NOT NULL,
    drivers_id bigint,
    vehicles_id bigint NOT NULL,
    fuel_log_id bigint,
    fecha date NOT NULL,
    kilometraje_salida numeric(10,2) NOT NULL,
    kilometraje_llegada numeric(10,2),
    recorrido_inicio character varying(255) NOT NULL,
    recorrido_destino character varying(255) NOT NULL,
    abastecimiento_combustible boolean DEFAULT false NOT NULL,
    firma_digital text,
    ruta_json json,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    latitud_inicio numeric(11,8),
    logitud_inicio numeric(11,8),
    latitud_destino numeric(11,8),
    logitud_destino numeric(11,8),
    kilometraje_recorrido numeric(10,2),
    odometro_photo_path character varying(255),
    session_reference character varying(255),
    responsible_driver_id bigint,
    current_driver_id bigint,
    activo boolean DEFAULT true NOT NULL,
    cantidad_paquetes integer
);

CREATE TABLE public.vehicle_log_investigation_tickets (
    id bigint NOT NULL,
    ticket_code character varying(40) NOT NULL,
    session_reference character varying(120) NOT NULL,
    vehicle_id bigint,
    responsible_driver_id bigint,
    current_driver_id bigint,
    related_user_id bigint,
    reason_type character varying(60) NOT NULL,
    status character varying(30) DEFAULT 'Abierto'::character varying NOT NULL,
    message text,
    packages_total integer DEFAULT 0 NOT NULL,
    packages_open integer DEFAULT 0 NOT NULL,
    packages_delivered integer DEFAULT 0 NOT NULL,
    meta_json json,
    opened_at timestamp(0) without time zone,
    closed_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.vehicle_log_sessions (
    id bigint NOT NULL,
    session_reference character varying(255) NOT NULL,
    vehicle_id bigint,
    responsible_driver_id bigint,
    current_driver_id bigint,
    origin_vehicle_log_id bigint,
    started_at timestamp(0) without time zone,
    last_reassigned_at timestamp(0) without time zone,
    ended_at timestamp(0) without time zone,
    status character varying(40) DEFAULT 'Activa'::character varying NOT NULL,
    meta_json json,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.vehicle_log_stage_events (
    id bigint NOT NULL,
    vehicle_log_session_id bigint,
    vehicle_log_id bigint,
    session_reference character varying(255),
    vehicle_id bigint,
    responsible_driver_id bigint,
    acting_driver_id bigint,
    stage_name character varying(60) NOT NULL,
    event_kind character varying(40) DEFAULT 'stage'::character varying NOT NULL,
    address character varying(255),
    latitude numeric(10,7),
    longitude numeric(11,7),
    event_at timestamp(0) without time zone,
    photo_path character varying(255),
    notes text,
    payload_json json,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.vehicle_operation_alerts (
    id bigint NOT NULL,
    vehicle_id bigint NOT NULL,
    vehicle_log_session_id bigint,
    alert_type character varying(40) NOT NULL,
    severity character varying(20) DEFAULT 'info'::character varying NOT NULL,
    status character varying(20) DEFAULT 'Activa'::character varying NOT NULL,
    title character varying(180) NOT NULL,
    message text,
    current_stage character varying(40),
    last_heartbeat_at timestamp(0) without time zone,
    detected_at timestamp(0) without time zone,
    resolved_at timestamp(0) without time zone,
    meta_json json,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.vehicles (
    id bigint NOT NULL,
    placa character varying(20) NOT NULL,
    marca character varying(50),
    modelo character varying(50),
    tipo_combustible character varying(30),
    color character varying(30),
    anio integer,
    capacidad_tanque numeric(10,2),
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    marca_id bigint,
    vehicle_class_id bigint,
    kilometraje numeric(10,2),
    kilometraje_inicial numeric(10,2),
    kilometraje_actual numeric(10,2),
    operational_status character varying(30) DEFAULT 'Disponible'::character varying NOT NULL,
    tacometro_danado boolean DEFAULT false NOT NULL,
    maintenance_form_type character varying(20),
    chasis character varying(80),
    motor character varying(80),
    kilometraje_inicial_photo_path character varying(255)
);

CREATE TABLE public.ventanilla (
    id bigint NOT NULL,
    nombre_ventanilla character varying(255) NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.window_load_metrics (
    id bigint NOT NULL,
    route_name character varying(190) NOT NULL,
    window_name character varying(180) NOT NULL,
    load_time_ms integer NOT NULL,
    server_time_ms integer,
    measured_at timestamp(0) without time zone NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone
);

CREATE TABLE public.workshop_catalogs (
    id bigint NOT NULL,
    nombre character varying(150) NOT NULL,
    tipo character varying(20) DEFAULT 'Interno'::character varying NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    user_id bigint,
    celular character varying(30)
);

CREATE TABLE public.workshop_part_changes (
    id bigint NOT NULL,
    workshop_id bigint NOT NULL,
    codigo_pieza_nueva character varying(120) NOT NULL,
    codigo_pieza_antigua character varying(120),
    descripcion character varying(255),
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    costo numeric(12,2)
);

CREATE TABLE public.workshops (
    id bigint NOT NULL,
    vehicle_id bigint NOT NULL,
    driver_id bigint,
    maintenance_appointment_id bigint,
    maintenance_log_id bigint,
    nombre_taller character varying(150) NOT NULL,
    fecha_ingreso date NOT NULL,
    fecha_salida date,
    estado character varying(40) DEFAULT 'Abierto'::character varying NOT NULL,
    pre_entrada_estado text NOT NULL,
    diagnostico text,
    observaciones text,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    workshop_catalog_id bigint,
    maintenance_alert_id bigint,
    order_number character varying(40),
    fecha_prometida_entrega date,
    fecha_listo date,
    observaciones_tecnicas text,
    workflow_kind character varying(20) DEFAULT 'Leve'::character varying NOT NULL,
    approval_required boolean DEFAULT false NOT NULL,
    fixed_catalog_cost numeric(10,2),
    labor_cost numeric(10,2),
    additional_cost numeric(10,2),
    total_cost numeric(10,2),
    diagnosis_requested_at timestamp(0) without time zone,
    fecha_aprobacion timestamp(0) without time zone,
    fecha_cierre timestamp(0) without time zone,
    dispatched_by_user_id bigint,
    diagnosed_by_user_id bigint,
    approved_by_user_id bigint,
    closed_by_user_id bigint,
    reassigned_from_workshop_catalog_id bigint,
    rejection_reason text,
    cancellation_reason text,
    reception_photo_path character varying(255),
    damage_photo_path character varying(255),
    invoice_file_path character varying(255),
    receipt_file_path character varying(255),
    activo boolean DEFAULT true NOT NULL
);

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.alerta_empresa_destinatarios
    ADD CONSTRAINT alerta_empresa_destinatarios_alerta_empresa_id_foreign FOREIGN KEY (alerta_empresa_id) REFERENCES public.alertas_empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.alerta_empresa_destinatarios
    ADD CONSTRAINT alerta_empresa_destinatarios_empresa_id_foreign FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.alerta_empresa_lecturas
    ADD CONSTRAINT alerta_empresa_lecturas_alerta_empresa_id_foreign FOREIGN KEY (alerta_empresa_id) REFERENCES public.alertas_empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.alerta_empresa_lecturas
    ADD CONSTRAINT alerta_empresa_lecturas_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.alerta_empresa_usuarios
    ADD CONSTRAINT alerta_empresa_usuarios_alerta_empresa_id_foreign FOREIGN KEY (alerta_empresa_id) REFERENCES public.alertas_empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.alerta_empresa_usuarios
    ADD CONSTRAINT alerta_empresa_usuarios_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.alertas_empresa
    ADD CONSTRAINT alertas_empresa_aprobada_por_foreign FOREIGN KEY (aprobada_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.alertas_empresa
    ADD CONSTRAINT alertas_empresa_creado_por_foreign FOREIGN KEY (creado_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.bitacoras
    ADD CONSTRAINT bitacoras_paquetes_certi_id_foreign FOREIGN KEY (paquetes_certi_id) REFERENCES public.paquetes_certi(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.bitacoras
    ADD CONSTRAINT bitacoras_paquetes_contrato_id_foreign FOREIGN KEY (paquetes_contrato_id) REFERENCES public.paquetes_contrato(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.bitacoras
    ADD CONSTRAINT bitacoras_paquetes_ems_id_foreign FOREIGN KEY (paquetes_ems_id) REFERENCES public.paquetes_ems(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.bitacoras
    ADD CONSTRAINT bitacoras_paquetes_ordi_id_foreign FOREIGN KEY (paquetes_ordi_id) REFERENCES public.paquetes_ordi(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.bitacoras
    ADD CONSTRAINT bitacoras_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.cartero_assignment_report_items
    ADD CONSTRAINT cartero_assignment_report_items_cartero_assignment_report_id_fo FOREIGN KEY (cartero_assignment_report_id) REFERENCES public.cartero_assignment_reports(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.cartero_assignment_reports
    ADD CONSTRAINT cartero_assignment_reports_actor_user_id_foreign FOREIGN KEY (actor_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cartero_assignment_reports
    ADD CONSTRAINT cartero_assignment_reports_assigned_user_id_foreign FOREIGN KEY (assigned_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cartero_guias
    ADD CONSTRAINT cartero_guias_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.cartero
    ADD CONSTRAINT cartero_id_estado_anterior_foreign FOREIGN KEY (id_estado_anterior) REFERENCES public.estados(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cartero
    ADD CONSTRAINT cartero_id_estados_foreign FOREIGN KEY (id_estados) REFERENCES public.estados(id);

ALTER TABLE ONLY public.cartero
    ADD CONSTRAINT cartero_id_paquetes_certi_foreign FOREIGN KEY (id_paquetes_certi) REFERENCES public.paquetes_certi(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cartero
    ADD CONSTRAINT cartero_id_paquetes_contrato_foreign FOREIGN KEY (id_paquetes_contrato) REFERENCES public.paquetes_contrato(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cartero
    ADD CONSTRAINT cartero_id_paquetes_ems_foreign FOREIGN KEY (id_paquetes_ems) REFERENCES public.paquetes_ems(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cartero
    ADD CONSTRAINT cartero_id_paquetes_ordi_foreign FOREIGN KEY (id_paquetes_ordi) REFERENCES public.paquetes_ordi(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cartero
    ADD CONSTRAINT cartero_id_solicitud_cliente_foreign FOREIGN KEY (id_solicitud_cliente) REFERENCES public.solicitud_clientes(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cartero
    ADD CONSTRAINT cartero_id_user_foreign FOREIGN KEY (id_user) REFERENCES public.users(id);

ALTER TABLE ONLY public.cashier_flow_receivable_collections
    ADD CONSTRAINT cashier_flow_receivable_collections_cobrado_por_foreign FOREIGN KEY (cobrado_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cashier_flow_receivable_collections
    ADD CONSTRAINT cashier_flow_receivable_collections_devuelto_por_foreign FOREIGN KEY (devuelto_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cashier_flow_receivable_movements
    ADD CONSTRAINT cashier_flow_receivable_movements_cobrado_por_foreign FOREIGN KEY (cobrado_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.cashier_flow_receivable_movements
    ADD CONSTRAINT cashier_flow_receivable_movements_devuelto_por_foreign FOREIGN KEY (devuelto_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.chasqui_location_points
    ADD CONSTRAINT chasqui_location_points_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.codigo_empresa
    ADD CONSTRAINT codigo_empresa_empresa_id_foreign FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.conciliaciones_empresa
    ADD CONSTRAINT conciliaciones_empresa_conciliacion_por_foreign FOREIGN KEY (conciliacion_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.conciliaciones_empresa
    ADD CONSTRAINT conciliaciones_empresa_conciliado_por_foreign FOREIGN KEY (conciliado_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.conciliaciones_empresa
    ADD CONSTRAINT conciliaciones_empresa_confirmacion_pago_por_foreign FOREIGN KEY (confirmacion_pago_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.conciliaciones_empresa
    ADD CONSTRAINT conciliaciones_empresa_documento_por_foreign FOREIGN KEY (documento_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.conciliaciones_empresa
    ADD CONSTRAINT conciliaciones_empresa_empresa_id_foreign FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.conciliaciones_empresa
    ADD CONSTRAINT conciliaciones_empresa_gestora_por_foreign FOREIGN KEY (gestora_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.conciliaciones_empresa
    ADD CONSTRAINT conciliaciones_empresa_pago_recibido_por_foreign FOREIGN KEY (pago_recibido_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.conciliaciones_empresa
    ADD CONSTRAINT conciliaciones_empresa_por_cobrar_por_foreign FOREIGN KEY (por_cobrar_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.despacho
    ADD CONSTRAINT despacho_fk_estado_foreign FOREIGN KEY (fk_estado) REFERENCES public.estados(id);

ALTER TABLE ONLY public.driver_incentive_reports
    ADD CONSTRAINT driver_incentive_reports_driver_id_foreign FOREIGN KEY (driver_id) REFERENCES public.drivers(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.empresa_historiales
    ADD CONSTRAINT empresa_historiales_archivado_por_foreign FOREIGN KEY (archivado_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.empresa_historiales
    ADD CONSTRAINT empresa_historiales_empresa_id_foreign FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.eventos_auditoria
    ADD CONSTRAINT eventos_auditoria_auditoria_id_foreign FOREIGN KEY (auditoria_id) REFERENCES public.auditoria(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_auditoria
    ADD CONSTRAINT eventos_auditoria_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_certi
    ADD CONSTRAINT eventos_certi_evento_id_foreign FOREIGN KEY (evento_id) REFERENCES public.eventos(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_certi
    ADD CONSTRAINT eventos_certi_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_contrato
    ADD CONSTRAINT eventos_contrato_evento_id_foreign FOREIGN KEY (evento_id) REFERENCES public.eventos(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_contrato
    ADD CONSTRAINT eventos_contrato_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_despacho
    ADD CONSTRAINT eventos_despacho_evento_id_foreign FOREIGN KEY (evento_id) REFERENCES public.eventos(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_despacho
    ADD CONSTRAINT eventos_despacho_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_ems
    ADD CONSTRAINT eventos_ems_evento_id_foreign FOREIGN KEY (evento_id) REFERENCES public.eventos(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_ems
    ADD CONSTRAINT eventos_ems_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_ordi
    ADD CONSTRAINT eventos_ordi_evento_id_foreign FOREIGN KEY (evento_id) REFERENCES public.eventos(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_ordi
    ADD CONSTRAINT eventos_ordi_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_tiktoker
    ADD CONSTRAINT eventos_tiktoker_cliente_id_foreign FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY public.eventos_tiktoker
    ADD CONSTRAINT eventos_tiktoker_evento_id_foreign FOREIGN KEY (evento_id) REFERENCES public.eventos(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.eventos_tiktoker
    ADD CONSTRAINT eventos_tiktoker_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY public.external_api_tokens
    ADD CONSTRAINT external_api_tokens_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_antifraud_cases
    ADD CONSTRAINT fuel_antifraud_cases_conflicting_driver_id_foreign FOREIGN KEY (conflicting_driver_id) REFERENCES public.drivers(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_antifraud_cases
    ADD CONSTRAINT fuel_antifraud_cases_conflicting_fuel_invoice_id_foreign FOREIGN KEY (conflicting_fuel_invoice_id) REFERENCES public.fuel_invoices(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_antifraud_cases
    ADD CONSTRAINT fuel_antifraud_cases_conflicting_vehicle_id_foreign FOREIGN KEY (conflicting_vehicle_id) REFERENCES public.vehicles(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_antifraud_cases
    ADD CONSTRAINT fuel_antifraud_cases_driver_id_foreign FOREIGN KEY (driver_id) REFERENCES public.drivers(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_antifraud_cases
    ADD CONSTRAINT fuel_antifraud_cases_fuel_invoice_id_foreign FOREIGN KEY (fuel_invoice_id) REFERENCES public.fuel_invoices(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_antifraud_cases
    ADD CONSTRAINT fuel_antifraud_cases_reviewed_by_user_id_foreign FOREIGN KEY (reviewed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_antifraud_cases
    ADD CONSTRAINT fuel_antifraud_cases_vehicle_id_foreign FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_invoice_details
    ADD CONSTRAINT fuel_invoice_details_fuel_invoice_id_foreign FOREIGN KEY (fuel_invoice_id) REFERENCES public.fuel_invoices(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.fuel_invoice_details
    ADD CONSTRAINT fuel_invoice_details_fuel_log_id_foreign FOREIGN KEY (fuel_log_id) REFERENCES public.fuel_logs(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_invoice_details
    ADD CONSTRAINT fuel_invoice_details_gas_station_id_foreign FOREIGN KEY (gas_station_id) REFERENCES public.gas_stations(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fuel_invoices
    ADD CONSTRAINT fuel_invoices_gas_station_id_foreign FOREIGN KEY (gas_station_id) REFERENCES public.gas_stations(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_alert_user_reads
    ADD CONSTRAINT maintenance_alert_user_reads_maintenance_alert_id_foreign FOREIGN KEY (maintenance_alert_id) REFERENCES public.maintenance_alerts(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.maintenance_alert_user_reads
    ADD CONSTRAINT maintenance_alert_user_reads_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.maintenance_alerts
    ADD CONSTRAINT maintenance_alerts_maintenance_appointment_id_foreign FOREIGN KEY (maintenance_appointment_id) REFERENCES public.maintenance_appointments(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_alerts
    ADD CONSTRAINT maintenance_alerts_maintenance_type_id_foreign FOREIGN KEY (maintenance_type_id) REFERENCES public.maintenance_types(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_alerts
    ADD CONSTRAINT maintenance_alerts_usuario_id_foreign FOREIGN KEY (usuario_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_alerts
    ADD CONSTRAINT maintenance_alerts_vehicle_id_foreign FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.maintenance_appointments
    ADD CONSTRAINT maintenance_appointments_approved_by_user_id_foreign FOREIGN KEY (approved_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_appointments
    ADD CONSTRAINT maintenance_appointments_driver_id_foreign FOREIGN KEY (driver_id) REFERENCES public.drivers(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_appointments
    ADD CONSTRAINT maintenance_appointments_requested_by_user_id_foreign FOREIGN KEY (requested_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_appointments
    ADD CONSTRAINT maintenance_appointments_tipo_mantenimiento_id_foreign FOREIGN KEY (tipo_mantenimiento_id) REFERENCES public.maintenance_types(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_appointments
    ADD CONSTRAINT maintenance_appointments_vehicle_id_foreign FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.maintenance_logs
    ADD CONSTRAINT maintenance_logs_maintenance_type_id_foreign FOREIGN KEY (maintenance_type_id) REFERENCES public.maintenance_types(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.maintenance_logs
    ADD CONSTRAINT maintenance_logs_vehicle_id_foreign FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.maintenance_type_vehicle
    ADD CONSTRAINT maintenance_type_vehicle_maintenance_type_id_foreign FOREIGN KEY (maintenance_type_id) REFERENCES public.maintenance_types(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.maintenance_type_vehicle
    ADD CONSTRAINT maintenance_type_vehicle_vehicle_id_foreign FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.malencaminados
    ADD CONSTRAINT malencaminados_paquetes_certi_id_foreign FOREIGN KEY (paquetes_certi_id) REFERENCES public.paquetes_certi(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.malencaminados
    ADD CONSTRAINT malencaminados_paquetes_contrato_id_foreign FOREIGN KEY (paquetes_contrato_id) REFERENCES public.paquetes_contrato(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.malencaminados
    ADD CONSTRAINT malencaminados_paquetes_ems_id_foreign FOREIGN KEY (paquetes_ems_id) REFERENCES public.paquetes_ems(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.malencaminados
    ADD CONSTRAINT malencaminados_paquetes_ordi_id_foreign FOREIGN KEY (paquetes_ordi_id) REFERENCES public.paquetes_ordi(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.malencaminados
    ADD CONSTRAINT malencaminados_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.mobile_db_snapshots
    ADD CONSTRAINT mobile_db_snapshots_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.model_has_permissions
    ADD CONSTRAINT model_has_permissions_permission_id_foreign FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.model_has_roles
    ADD CONSTRAINT model_has_roles_role_id_foreign FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.paquetes_certi
    ADD CONSTRAINT paquetes_certi_fk_estado_foreign FOREIGN KEY (fk_estado) REFERENCES public.estados(id);

ALTER TABLE ONLY public.paquetes_certi
    ADD CONSTRAINT paquetes_certi_fk_ventanilla_foreign FOREIGN KEY (fk_ventanilla) REFERENCES public.ventanilla(id);

ALTER TABLE ONLY public.paquetes_certi
    ADD CONSTRAINT paquetes_certi_servicio_id_foreign FOREIGN KEY (servicio_id) REFERENCES public.servicio(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.paquetes_contrato
    ADD CONSTRAINT paquetes_contrato_empresa_id_foreign FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.paquetes_contrato
    ADD CONSTRAINT paquetes_contrato_estados_id_foreign FOREIGN KEY (estados_id) REFERENCES public.estados(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.paquetes_contrato
    ADD CONSTRAINT paquetes_contrato_tarifa_contrato_id_foreign FOREIGN KEY (tarifa_contrato_id) REFERENCES public.tarifa_contrato(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY public.paquetes_ems
    ADD CONSTRAINT paquetes_ems_estado_id_foreign FOREIGN KEY (estado_id) REFERENCES public.estados(id);

ALTER TABLE ONLY public.paquetes_ems_formulario
    ADD CONSTRAINT paquetes_ems_formulario_paquete_ems_id_foreign FOREIGN KEY (paquete_ems_id) REFERENCES public.paquetes_ems(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.paquetes_ems
    ADD CONSTRAINT paquetes_ems_tarifario_id_foreign FOREIGN KEY (tarifario_id) REFERENCES public.tarifario(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.paquetes_ems
    ADD CONSTRAINT paquetes_ems_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.paquetes_ordi
    ADD CONSTRAINT paquetes_ordi_fk_estado_foreign FOREIGN KEY (fk_estado) REFERENCES public.estados(id);

ALTER TABLE ONLY public.paquetes_ordi
    ADD CONSTRAINT paquetes_ordi_fk_ventanilla_foreign FOREIGN KEY (fk_ventanilla) REFERENCES public.ventanilla(id);

ALTER TABLE ONLY public.paquetes_ordi
    ADD CONSTRAINT paquetes_ordi_servicio_id_foreign FOREIGN KEY (servicio_id) REFERENCES public.servicio(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.preregistros
    ADD CONSTRAINT preregistros_destino_id_foreign FOREIGN KEY (destino_id) REFERENCES public.destino(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.preregistros
    ADD CONSTRAINT preregistros_paquete_ems_id_foreign FOREIGN KEY (paquete_ems_id) REFERENCES public.paquetes_ems(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.preregistros
    ADD CONSTRAINT preregistros_servicio_id_foreign FOREIGN KEY (servicio_id) REFERENCES public.servicio(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.preregistros
    ADD CONSTRAINT preregistros_validado_por_foreign FOREIGN KEY (validado_por) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.paquetes_contrato
    ADD CONSTRAINT recojos_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.role_has_permissions
    ADD CONSTRAINT role_has_permissions_permission_id_foreign FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.role_has_permissions
    ADD CONSTRAINT role_has_permissions_role_id_foreign FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.saca
    ADD CONSTRAINT saca_fk_despacho_foreign FOREIGN KEY (fk_despacho) REFERENCES public.despacho(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.saca
    ADD CONSTRAINT saca_fk_estado_foreign FOREIGN KEY (fk_estado) REFERENCES public.estados(id);

ALTER TABLE ONLY public.solicitud_clientes
    ADD CONSTRAINT solicitud_clientes_cliente_id_foreign FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.solicitud_clientes
    ADD CONSTRAINT solicitud_clientes_destino_id_foreign FOREIGN KEY (destino_id) REFERENCES public.destino(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.solicitud_clientes
    ADD CONSTRAINT solicitud_clientes_estado_id_foreign FOREIGN KEY (estado_id) REFERENCES public.estados(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.solicitud_clientes
    ADD CONSTRAINT solicitud_clientes_servicio_extra_id_foreign FOREIGN KEY (servicio_extra_id) REFERENCES public.servicio_extras(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY public.solicitud_clientes
    ADD CONSTRAINT solicitud_clientes_servicio_id_foreign FOREIGN KEY (servicio_id) REFERENCES public.servicio(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.solicitud_clientes
    ADD CONSTRAINT solicitud_clientes_tarifario_tiktoker_id_foreign FOREIGN KEY (tarifario_tiktoker_id) REFERENCES public.tarifario_tiktoker(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY public.tarifa_contrato
    ADD CONSTRAINT tarifa_contrato_empresa_id_foreign FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.tarifario
    ADD CONSTRAINT tarifario_destino_id_foreign FOREIGN KEY (destino_id) REFERENCES public.destino(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.tarifario
    ADD CONSTRAINT tarifario_origen_id_foreign FOREIGN KEY (origen_id) REFERENCES public.origen(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.tarifario
    ADD CONSTRAINT tarifario_peso_id_foreign FOREIGN KEY (peso_id) REFERENCES public.peso(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.tarifario
    ADD CONSTRAINT tarifario_servicio_id_foreign FOREIGN KEY (servicio_id) REFERENCES public.servicio(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.tarifario_tiktoker
    ADD CONSTRAINT tarifario_tiktoker_destino_id_foreign FOREIGN KEY (destino_id) REFERENCES public.destino(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.tarifario_tiktoker
    ADD CONSTRAINT tarifario_tiktoker_origen_id_foreign FOREIGN KEY (origen_id) REFERENCES public.origen(id) ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY public.tarifario_tiktoker
    ADD CONSTRAINT tarifario_tiktoker_servicio_extra_id_foreign FOREIGN KEY (servicio_extra_id) REFERENCES public.servicio_extras(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY public.telescope_entries_tags
    ADD CONSTRAINT telescope_entries_tags_entry_uuid_foreign FOREIGN KEY (entry_uuid) REFERENCES public.telescope_entries(uuid) ON DELETE CASCADE;

ALTER TABLE ONLY public.user_ips_links
    ADD CONSTRAINT user_ips_links_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY public.user_login_logs
    ADD CONSTRAINT user_login_logs_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_empresa_id_foreign FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_foreign FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_sucursal_id_foreign FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY public.vehicle_assignments
    ADD CONSTRAINT vehicle_assignments_driver_id_foreign FOREIGN KEY (driver_id) REFERENCES public.drivers(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.vehicle_assignments
    ADD CONSTRAINT vehicle_assignments_vehicle_id_foreign FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.vehicle_log
    ADD CONSTRAINT vehicle_log_drivers_id_foreign FOREIGN KEY (drivers_id) REFERENCES public.drivers(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.vehicle_log
    ADD CONSTRAINT vehicle_log_fuel_log_id_foreign FOREIGN KEY (fuel_log_id) REFERENCES public.fuel_invoice_details(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.vehicle_log_investigation_tickets
    ADD CONSTRAINT vehicle_log_investigation_tickets_current_driver_id_foreign FOREIGN KEY (current_driver_id) REFERENCES public.drivers(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.vehicle_log_investigation_tickets
    ADD CONSTRAINT vehicle_log_investigation_tickets_related_user_id_foreign FOREIGN KEY (related_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.vehicle_log_investigation_tickets
    ADD CONSTRAINT vehicle_log_investigation_tickets_responsible_driver_id_foreign FOREIGN KEY (responsible_driver_id) REFERENCES public.drivers(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.vehicle_log_investigation_tickets
    ADD CONSTRAINT vehicle_log_investigation_tickets_vehicle_id_foreign FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.vehicle_log
    ADD CONSTRAINT vehicle_log_vehicles_id_foreign FOREIGN KEY (vehicles_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.workshop_catalogs
    ADD CONSTRAINT workshop_catalogs_user_id_foreign FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshop_part_changes
    ADD CONSTRAINT workshop_part_changes_workshop_id_foreign FOREIGN KEY (workshop_id) REFERENCES public.workshops(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_approved_by_user_id_foreign FOREIGN KEY (approved_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_closed_by_user_id_foreign FOREIGN KEY (closed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_diagnosed_by_user_id_foreign FOREIGN KEY (diagnosed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_dispatched_by_user_id_foreign FOREIGN KEY (dispatched_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_driver_id_foreign FOREIGN KEY (driver_id) REFERENCES public.drivers(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_maintenance_alert_id_foreign FOREIGN KEY (maintenance_alert_id) REFERENCES public.maintenance_alerts(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_maintenance_appointment_id_foreign FOREIGN KEY (maintenance_appointment_id) REFERENCES public.maintenance_appointments(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_maintenance_log_id_foreign FOREIGN KEY (maintenance_log_id) REFERENCES public.maintenance_logs(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_reassigned_from_workshop_catalog_id_foreign FOREIGN KEY (reassigned_from_workshop_catalog_id) REFERENCES public.workshop_catalogs(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_vehicle_id_foreign FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_workshop_catalog_id_foreign FOREIGN KEY (workshop_catalog_id) REFERENCES public.workshop_catalogs(id) ON DELETE SET NULL;
