-- Table: public.yolo

-- DROP TABLE IF EXISTS public.yolo;

CREATE TABLE IF NOT EXISTS public.yolo
(
    job_id uuid NOT NULL,
    frame_id integer NOT NULL,
    result jsonb,
    CONSTRAINT yolo_pkey PRIMARY KEY (job_id, frame_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.yolo
    OWNER to postgres;