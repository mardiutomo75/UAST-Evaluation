-- Adminer 5.4.2 PostgreSQL 17.9 dump

DROP FUNCTION IF EXISTS "refresh_pec_result";;
CREATE FUNCTION "refresh_pec_result" () RETURNS void LANGUAGE sql AS '
    REFRESH MATERIALIZED VIEW pec_result_cache;
';

DROP TABLE IF EXISTS "c2c_cs";
DROP SEQUENCE IF EXISTS "public".c2c_cs_id_seq;
CREATE SEQUENCE "public".c2c_cs_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2c_cs" (
    "id" bigint DEFAULT nextval('c2c_cs_id_seq') NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255),
    "code" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "ted" numeric,
    "normal" numeric,
    "similarity" numeric,
    "ted2" numeric,
    "ted3" numeric,
    "ted4" numeric,
    "simbert" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2c_cs_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE INDEX c2c_cs_split ON public.c2c_cs USING btree (split);

CREATE INDEX c2c_cs_status ON public.c2c_cs USING btree (status);

CREATE INDEX c2c_cs_f1_precision_recall_reconstruction_bleu ON public.c2c_cs USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2c_java";
DROP SEQUENCE IF EXISTS "public".c2c_java_id_seq;
CREATE SEQUENCE "public".c2c_java_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2c_java" (
    "id" bigint DEFAULT nextval('c2c_java_id_seq') NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255),
    "code" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "ted" numeric,
    "normal" numeric,
    "similarity" numeric,
    "ted3" numeric,
    "ted4" numeric,
    "ted2" numeric,
    "simbert" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2c_java_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE INDEX c2c_java_split ON public.c2c_java USING btree (split);

CREATE INDEX c2c_java_status ON public.c2c_java USING btree (status);

CREATE INDEX c2c_java_f1_precision_recall_reconstruction_bleu ON public.c2c_java USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_cpp";
DROP SEQUENCE IF EXISTS "public".c2t_cpp_id_seq;
CREATE SEQUENCE "public".c2t_cpp_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_cpp" (
    "id" bigint DEFAULT nextval('c2t_cpp_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_cpp_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_cpp ON public.c2t_cpp USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_cpp_split ON public.c2t_cpp USING btree (split);

CREATE INDEX c2t_cpp_status ON public.c2t_cpp USING btree (status);

CREATE INDEX c2t_cpp_f1_precision_recall_reconstruction_bleu ON public.c2t_cpp USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_cs";
DROP SEQUENCE IF EXISTS "public".c2t_cs_id_seq;
CREATE SEQUENCE "public".c2t_cs_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_cs" (
    "id" bigint DEFAULT nextval('c2t_cs_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_cs_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_cs ON public.c2t_cs USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_cs_split ON public.c2t_cs USING btree (split);

CREATE INDEX c2t_cs_status ON public.c2t_cs USING btree (status);

CREATE INDEX c2t_cs_f1_precision_recall_reconstruction_bleu ON public.c2t_cs USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_go";
DROP SEQUENCE IF EXISTS "public".c2t_go_id_seq;
CREATE SEQUENCE "public".c2t_go_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_go" (
    "id" bigint DEFAULT nextval('c2t_go_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_go_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_go ON public.c2t_go USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_go_split ON public.c2t_go USING btree (split);

CREATE INDEX c2t_go_status ON public.c2t_go USING btree (status);

CREATE INDEX c2t_go_f1_precision_recall_reconstruction_bleu ON public.c2t_go USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_java";
DROP SEQUENCE IF EXISTS "public".c2t_java_id_seq;
CREATE SEQUENCE "public".c2t_java_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_java" (
    "id" bigint DEFAULT nextval('c2t_java_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_java_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_java ON public.c2t_java USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_java_split ON public.c2t_java USING btree (split);

CREATE INDEX c2t_java_status ON public.c2t_java USING btree (status);

CREATE INDEX c2t_java_f1_precision_recall_reconstruction_bleu ON public.c2t_java USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_javascript";
DROP SEQUENCE IF EXISTS "public".c2t_javascript_id_seq;
CREATE SEQUENCE "public".c2t_javascript_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_javascript" (
    "id" bigint DEFAULT nextval('c2t_javascript_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_javascript_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_javascript ON public.c2t_javascript USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_javascript_split ON public.c2t_javascript USING btree (split);

CREATE INDEX c2t_javascript_status ON public.c2t_javascript USING btree (status);

CREATE INDEX c2t_javascript_f1_precision_recall_reconstruction_b ON public.c2t_javascript USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_php";
DROP SEQUENCE IF EXISTS "public".c2t_php_id_seq;
CREATE SEQUENCE "public".c2t_php_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_php" (
    "id" bigint DEFAULT nextval('c2t_php_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_php_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_php ON public.c2t_php USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_php_split ON public.c2t_php USING btree (split);

CREATE INDEX c2t_php_status ON public.c2t_php USING btree (status);

CREATE INDEX c2t_php_f1_precision_recall_reconstruction_bleu ON public.c2t_php USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_python";
DROP SEQUENCE IF EXISTS "public".c2t_python_id_seq;
CREATE SEQUENCE "public".c2t_python_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_python" (
    "id" bigint DEFAULT nextval('c2t_python_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_python_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_python ON public.c2t_python USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_python_split ON public.c2t_python USING btree (split);

CREATE INDEX c2t_python_status ON public.c2t_python USING btree (status);

CREATE INDEX c2t_python_f1_precision_recall_reconstruction_bleu ON public.c2t_python USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_ruby";
DROP SEQUENCE IF EXISTS "public".c2t_ruby_id_seq;
CREATE SEQUENCE "public".c2t_ruby_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_ruby" (
    "id" bigint DEFAULT nextval('c2t_ruby_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_ruby_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_ruby ON public.c2t_ruby USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_ruby_split ON public.c2t_ruby USING btree (split);

CREATE INDEX c2t_ruby_status ON public.c2t_ruby USING btree (status);

CREATE INDEX c2t_ruby_f1_precision_recall_reconstruction_bleu ON public.c2t_ruby USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "c2t_rust";
DROP SEQUENCE IF EXISTS "public".c2t_rust_id_seq;
CREATE SEQUENCE "public".c2t_rust_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."c2t_rust" (
    "id" bigint DEFAULT nextval('c2t_rust_id_seq') NOT NULL,
    "repo" character varying(255) NOT NULL,
    "path" character varying(255) NOT NULL,
    "split" character varying(20) NOT NULL,
    "func_name" character varying(255) NOT NULL,
    "original_string" text NOT NULL,
    "code" text NOT NULL,
    "code_tokens" text NOT NULL,
    "docstring" text NOT NULL,
    "docstring_tokens" text NOT NULL,
    "status" smallint DEFAULT '0' NOT NULL,
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "c2t_rust_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_c2t_rust ON public.c2t_rust USING btree (func_name, split, docstring_tokens);

CREATE INDEX c2t_rust_split ON public.c2t_rust USING btree (split);

CREATE INDEX c2t_rust_status ON public.c2t_rust USING btree (status);

CREATE INDEX c2t_rust_f1_precision_recall_reconstruction_bleu ON public.c2t_rust USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "heval";
DROP SEQUENCE IF EXISTS "public".heval_id_seq;
CREATE SEQUENCE "public".heval_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."heval" (
    "id" bigint DEFAULT nextval('heval_id_seq') NOT NULL,
    "language" character varying(32) NOT NULL,
    "repo" character varying(255),
    "path" character varying(255),
    "split" character varying(20),
    "func_name" character varying(255),
    "original_string" text,
    "code" text,
    "code_tokens" text,
    "docstring" text,
    "docstring_tokens" text,
    "status" smallint DEFAULT '1',
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_heval ON public.heval USING btree (language, func_name);

CREATE INDEX heval_split ON public.heval USING btree (split);

CREATE INDEX heval_status ON public.heval USING btree (status);

CREATE INDEX heval_f1_precision_recall_reconstruction_bleu ON public.heval USING btree (f1, "precision", recall, reconstruction_bleu);

CREATE INDEX heval_language ON public.heval USING btree (language);

CREATE INDEX heval_language_split ON public.heval USING btree (language, split);


DROP TABLE IF EXISTS "heval_cpp";
DROP SEQUENCE IF EXISTS "public".heval_cpp_id_seq;
CREATE SEQUENCE "public".heval_cpp_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."heval_cpp" (
    "id" bigint DEFAULT nextval('heval_cpp_id_seq') NOT NULL,
    "repo" character varying(255),
    "path" character varying(255),
    "split" character varying(20),
    "func_name" character varying(255),
    "original_string" text,
    "code" text,
    "code_tokens" text,
    "docstring" text,
    "docstring_tokens" text,
    "status" smallint DEFAULT '1',
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "ted" numeric,
    "normal" numeric,
    "similarity" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "heval_cpp_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_heval_cpp ON public.heval_cpp USING btree (func_name, split, docstring_tokens);

CREATE INDEX heval_cpp_split ON public.heval_cpp USING btree (split);

CREATE INDEX heval_cpp_status ON public.heval_cpp USING btree (status);

CREATE INDEX heval_cpp_f1_precision_recall_reconstruction_bleu ON public.heval_cpp USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "heval_go";
DROP SEQUENCE IF EXISTS "public".heval_go_id_seq;
CREATE SEQUENCE "public".heval_go_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."heval_go" (
    "id" bigint DEFAULT nextval('heval_go_id_seq') NOT NULL,
    "repo" character varying(255),
    "path" character varying(255),
    "split" character varying(20),
    "func_name" character varying(255),
    "original_string" text,
    "code" text,
    "code_tokens" text,
    "docstring" text,
    "docstring_tokens" text,
    "status" smallint DEFAULT '1',
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "ted" numeric,
    "normal" numeric,
    "similarity" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "heval_go_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_heval_go ON public.heval_go USING btree (func_name, split, docstring_tokens);

CREATE INDEX heval_go_split ON public.heval_go USING btree (split);

CREATE INDEX heval_go_status ON public.heval_go USING btree (status);

CREATE INDEX heval_go_f1_precision_recall_reconstruction_bleu ON public.heval_go USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "heval_java";
DROP SEQUENCE IF EXISTS "public".heval_java_id_seq;
CREATE SEQUENCE "public".heval_java_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."heval_java" (
    "id" bigint DEFAULT nextval('heval_java_id_seq') NOT NULL,
    "repo" character varying(255),
    "path" character varying(255),
    "split" character varying(20),
    "func_name" character varying(255),
    "original_string" text,
    "code" text,
    "code_tokens" text,
    "docstring" text,
    "docstring_tokens" text,
    "status" smallint DEFAULT '1',
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "ted" numeric,
    "normal" numeric,
    "similarity" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "heval_java_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_heval_java ON public.heval_java USING btree (func_name, split, docstring_tokens);

CREATE INDEX heval_java_split ON public.heval_java USING btree (split);

CREATE INDEX heval_java_status ON public.heval_java USING btree (status);

CREATE INDEX heval_java_f1_precision_recall_reconstruction_bleu ON public.heval_java USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "heval_javascript";
DROP SEQUENCE IF EXISTS "public".heval_javascript_id_seq;
CREATE SEQUENCE "public".heval_javascript_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."heval_javascript" (
    "id" bigint DEFAULT nextval('heval_javascript_id_seq') NOT NULL,
    "repo" character varying(255),
    "path" character varying(255),
    "split" character varying(20),
    "func_name" character varying(255),
    "original_string" text,
    "code" text,
    "code_tokens" text,
    "docstring" text,
    "docstring_tokens" text,
    "status" smallint DEFAULT '1',
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "ted" numeric,
    "normal" numeric,
    "similarity" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "heval_javascript_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_heval_javascript ON public.heval_javascript USING btree (func_name, split, docstring_tokens);

CREATE INDEX heval_javascript_split ON public.heval_javascript USING btree (split);

CREATE INDEX heval_javascript_status ON public.heval_javascript USING btree (status);

CREATE INDEX heval_javascript_f1_precision_recall_reconstruction ON public.heval_javascript USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "heval_matrix";
DROP SEQUENCE IF EXISTS "public".heval_matrix_id_seq;
CREATE SEQUENCE "public".heval_matrix_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."heval_matrix" (
    "id" bigint DEFAULT nextval('heval_matrix_id_seq') NOT NULL,
    "language1" character varying(20) NOT NULL,
    "language2" character varying(20) NOT NULL,
    "ted" numeric NOT NULL,
    "similarity" numeric NOT NULL,
    "normal" numeric NOT NULL,
    "func_id" integer NOT NULL,
    "ted2" numeric,
    "ted3" numeric,
    "ted4" numeric,
    "simbert" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "heval_matrix_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_heval_matrix_pair ON public.heval_matrix USING btree (language1, language2, func_id);


DROP TABLE IF EXISTS "heval_python";
DROP SEQUENCE IF EXISTS "public".heval_python_id_seq;
CREATE SEQUENCE "public".heval_python_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."heval_python" (
    "id" bigint DEFAULT nextval('heval_python_id_seq') NOT NULL,
    "repo" character varying(255),
    "path" character varying(255),
    "split" character varying(20),
    "func_name" character varying(255),
    "original_string" text,
    "code" text,
    "code_tokens" text,
    "docstring" text,
    "docstring_tokens" text,
    "status" smallint DEFAULT '1',
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "ted" numeric,
    "normal" numeric,
    "similarity" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "heval_python_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_heval_python ON public.heval_python USING btree (func_name, split, docstring_tokens);

CREATE INDEX heval_python_split ON public.heval_python USING btree (split);

CREATE INDEX heval_python_status ON public.heval_python USING btree (status);

CREATE INDEX heval_python_f1_precision_recall_reconstruction_ble ON public.heval_python USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "heval_rust";
DROP SEQUENCE IF EXISTS "public".heval_rust_id_seq;
CREATE SEQUENCE "public".heval_rust_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."heval_rust" (
    "id" bigint DEFAULT nextval('heval_rust_id_seq') NOT NULL,
    "repo" character varying(255),
    "path" character varying(255),
    "split" character varying(20),
    "func_name" character varying(255),
    "original_string" text,
    "code" text,
    "code_tokens" text,
    "docstring" text,
    "docstring_tokens" text,
    "status" smallint DEFAULT '1',
    "ast_original" text,
    "ast_unified" text,
    "f1" numeric,
    "precision" numeric,
    "recall" numeric,
    "reconstruction_bleu" numeric,
    "compression_ratio" numeric,
    "ast_error" text,
    "ast_status" integer DEFAULT '0',
    "var_original" jsonb,
    "func_original" jsonb,
    "var_unified" jsonb,
    "func_unified" jsonb,
    "ted" numeric,
    "normal" numeric,
    "similarity" numeric,
    "attribut_ori" integer,
    "attribut_uni" integer,
    "attribut_loss" numeric,
    "dmem" numeric,
    "dtime" numeric,
    "dmem1" numeric,
    "dtime1" numeric,
    "dmem2" numeric,
    "dtime2" numeric,
    "dmem3" numeric,
    "dtime3" numeric,
    "pec_score" numeric,
    "pec_score_all" numeric,
    "pec_data" jsonb,
    CONSTRAINT "heval_rust_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX unique_heval_rust ON public.heval_rust USING btree (func_name, split, docstring_tokens);

CREATE INDEX heval_rust_split ON public.heval_rust USING btree (split);

CREATE INDEX heval_rust_status ON public.heval_rust USING btree (status);

CREATE INDEX heval_rust_f1_precision_recall_reconstruction_bleu ON public.heval_rust USING btree (f1, "precision", recall, reconstruction_bleu);


DROP TABLE IF EXISTS "languages";
DROP SEQUENCE IF EXISTS "public".languages_id_seq;
CREATE SEQUENCE "public".languages_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TABLE "public"."languages" (
    "id" integer DEFAULT nextval('languages_id_seq') NOT NULL,
    "name" character varying(15) NOT NULL,
    CONSTRAINT "languages_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

INSERT INTO "languages" ("id", "name") VALUES
(1,	'go'),
(2,	'python'),
(3,	'ruby'),
(4,	'php'),
(5,	'java'),
(6,	'javascript'),
(7,	'cpp'),
(8,	'rust');

DROP TABLE IF EXISTS "nodes";
DROP SEQUENCE IF EXISTS "public".nodes_id_seq;
CREATE SEQUENCE "public".nodes_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TABLE "public"."nodes" (
    "id" integer DEFAULT nextval('nodes_id_seq') NOT NULL,
    "language" character varying(20) NOT NULL,
    "category" character varying(200) NOT NULL,
    "node_type" character varying(200) NOT NULL,
    "count" bigint NOT NULL,
    CONSTRAINT "nodes_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE INDEX nodes_language ON public.nodes USING btree (language);

CREATE UNIQUE INDEX nodes_language_category_node_type ON public.nodes USING btree (language, category, node_type);


DROP VIEW IF EXISTS "statistik_deskriptif";
CREATE TABLE "statistik_deskriptif" ("Dataset" text, "Metrik" text, "Mean" text, "Std. Dev." text, "Min" text, "Max" text);


DROP TABLE IF EXISTS "statuses";
DROP SEQUENCE IF EXISTS "public".statuses_id_seq;
CREATE SEQUENCE "public".statuses_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 32767 CACHE 1;

CREATE TABLE "public"."statuses" (
    "id" smallint DEFAULT nextval('statuses_id_seq') NOT NULL,
    "name" character varying(100) NOT NULL,
    CONSTRAINT "statuses_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

INSERT INTO "statuses" ("id", "name") VALUES
(1,	'active'),
(2,	'parsed'),
(3,	'parsing failed'),
(4,	'unified'),
(5,	'unified failed');

DROP VIEW IF EXISTS "v_c2c_metrics";
CREATE TABLE "v_c2c_metrics" ("language1" text, "language2" text, "ted_uast_uast_mean" numeric, "ted_uast_uast_std_dev" numeric, "ted_uast_uast_min" numeric, "ted_uast_uast_max" numeric, "ted_uast_original_mean" numeric, "ted_uast_original_std_dev" numeric, "ted_uast_original_min" numeric, "ted_uast_original_max" numeric, "ted_original_uast_mean" numeric, "ted_original_uast_std_dev" numeric, "ted_original_uast_min" numeric, "ted_original_uast_max" numeric, "ted_original_original_mean" numeric, "ted_original_original_std_dev" numeric, "ted_original_original_min" numeric, "ted_original_original_max" numeric, "cosine_similarity_mean" numeric, "cosine_similarity_std_dev" numeric, "cosine_similarity_min" numeric, "cosine_similarity_max" numeric, "reconstruction_bleu_mean" numeric, "reconstruction_bleu_std_dev" numeric, "reconstruction_bleu_min" numeric, "reconstruction_bleu_max" numeric, "compression_ratio_mean" numeric, "compression_ratio_std_dev" numeric, "compression_ratio_min" numeric, "compression_ratio_max" numeric, "f1_mean" numeric, "f1_std_dev" numeric, "f1_min" numeric, "f1_max" numeric, "precision_mean" numeric, "precision_std_dev" numeric, "precision_min" numeric, "precision_max" numeric, "recall_mean" numeric, "recall_std_dev" numeric, "recall_min" numeric, "recall_max" numeric, "dmem_mean" numeric, "dmem_std_dev" numeric, "dmem_min" numeric, "dmem_max" numeric, "dtime_mean" numeric, "dtime_std_dev" numeric, "dtime_min" numeric, "dtime_max" numeric, "attribut_loss_mean" numeric, "attribut_loss_std_dev" numeric, "attribut_loss_min" numeric, "attribut_loss_max" numeric, "pec_score_mean" numeric, "pec_score_std_dev" numeric, "pec_score_min" numeric, "pec_score_max" numeric, "pec_score_all_mean" numeric, "pec_score_all_std_dev" numeric, "pec_score_all_min" numeric, "pec_score_all_max" numeric);


DROP VIEW IF EXISTS "v_humaneval_metrics";
CREATE TABLE "v_humaneval_metrics" ("language" text, "cosine_similarity" numeric, "compression_ratio" numeric, "reconstruction_bleu" numeric, "f1" numeric, "precision" numeric, "recall" numeric, "ast_time_ms" numeric, "total_time_ms" numeric, "uast_extra_time_ms" numeric, "ast_memory_mb" numeric, "total_memory_mb" numeric, "uast_extra_memory_mb" numeric, "time_overhead_percent" numeric, "memory_overhead_percent" numeric, "attribut_loss" numeric);


DROP VIEW IF EXISTS "vstat_c2c";
CREATE TABLE "vstat_c2c" ("language1" text, "language2" text, "ted_uast_uast_mean" numeric, "ted_uast_uast_std_dev" numeric, "ted_uast_uast_min" numeric, "ted_uast_uast_max" numeric, "ted_uast_original_mean" numeric, "ted_uast_original_std_dev" numeric, "ted_uast_original_min" numeric, "ted_uast_original_max" numeric, "ted_original_uast_mean" numeric, "ted_original_uast_std_dev" numeric, "ted_original_uast_min" numeric, "ted_original_uast_max" numeric, "ted_original_original_mean" numeric, "ted_original_original_std_dev" numeric, "ted_original_original_min" numeric, "ted_original_original_max" numeric, "cosine_similarity_mean" numeric, "cosine_similarity_std_dev" numeric, "cosine_similarity_min" numeric, "cosine_similarity_max" numeric, "reconstruction_bleu_mean" numeric, "reconstruction_bleu_std_dev" numeric, "reconstruction_bleu_min" numeric, "reconstruction_bleu_max" numeric, "compression_ratio_mean" numeric, "compression_ratio_std_dev" numeric, "compression_ratio_min" numeric, "compression_ratio_max" numeric, "f1_mean" numeric, "f1_std_dev" numeric, "f1_min" numeric, "f1_max" numeric, "precision_mean" numeric, "precision_std_dev" numeric, "precision_min" numeric, "precision_max" numeric, "recall_mean" numeric, "recall_std_dev" numeric, "recall_min" numeric, "recall_max" numeric, "dmem_mean" numeric, "dmem_std_dev" numeric, "dmem_min" numeric, "dmem_max" numeric, "dtime_mean" numeric, "dtime_std_dev" numeric, "dtime_min" numeric, "dtime_max" numeric, "attribut_loss_mean" numeric, "attribut_loss_std_dev" numeric, "attribut_loss_min" numeric, "attribut_loss_max" numeric, "pec_score_mean" numeric, "pec_score_std_dev" numeric, "pec_score_min" numeric, "pec_score_max" numeric, "pec_score_all_mean" numeric, "pec_score_all_std_dev" numeric, "pec_score_all_min" numeric, "pec_score_all_max" numeric);


DROP VIEW IF EXISTS "vstat_c2t";
CREATE TABLE "vstat_c2t" ("language" text, "compression_ratio" numeric, "bleu" numeric, "f1" numeric, "precision" numeric, "recall" numeric, "dmem" numeric, "dtime" numeric, "attribut_loss" numeric);


DROP VIEW IF EXISTS "vstat_heval";
CREATE TABLE "vstat_heval" ("language" text, "cosine_similarity_mean" numeric, "cosine_similarity_std_dev" numeric, "cosine_similarity_min" numeric, "cosine_similarity_max" numeric, "compression_ratio_mean" numeric, "compression_ratio_std_dev" numeric, "compression_ratio_min" numeric, "compression_ratio_max" numeric, "reconstruction_bleu_mean" numeric, "reconstruction_bleu_std_dev" numeric, "reconstruction_bleu_min" numeric, "reconstruction_bleu_max" numeric, "f1_mean" numeric, "f1_std_dev" numeric, "f1_min" numeric, "f1_max" numeric, "precision_mean" numeric, "precision_std_dev" numeric, "precision_min" numeric, "precision_max" numeric, "recall_mean" numeric, "recall_std_dev" numeric, "recall_min" numeric, "recall_max" numeric, "dmem_mean" numeric, "dmem_std_dev" numeric, "dmem_min" numeric, "dmem_max" numeric, "dtime_mean" numeric, "dtime_std_dev" numeric, "dtime_min" numeric, "dtime_max" numeric, "attribut_loss_mean" numeric, "attribut_loss_std_dev" numeric, "attribut_loss_min" numeric, "attribut_loss_max" numeric, "pec_score_mean" numeric, "pec_score_std_dev" numeric, "pec_score_min" numeric, "pec_score_max" numeric, "pec_score_all_mean" numeric, "pec_score_all_std_dev" numeric, "pec_score_all_min" numeric, "pec_score_all_max" numeric);


DROP VIEW IF EXISTS "vted_heval";
CREATE TABLE "vted_heval" ("language1" character varying(20), "language2" character varying(20), "ted_uast_uast_mean" numeric, "ted_uast_uast_std_dev" numeric, "ted_uast_uast_min" numeric, "ted_uast_uast_max" numeric, "ted_uast_original_mean" numeric, "ted_uast_original_std_dev" numeric, "ted_uast_original_min" numeric, "ted_uast_original_max" numeric, "ted_original_uast_mean" numeric, "ted_original_uast_std_dev" numeric, "ted_original_uast_min" numeric, "ted_original_uast_max" numeric, "ted_original_original_mean" numeric, "ted_original_original_std_dev" numeric, "ted_original_original_min" numeric, "ted_original_original_max" numeric, "cosine_similarity_mean" numeric, "cosine_similarity_std_dev" numeric, "cosine_similarity_min" numeric, "cosine_similarity_max" numeric);


DROP MATERIALIZED VIEW IF EXISTS "pec_result_cache";
DROP TABLE IF EXISTS "pec_result_cache";
CREATE MATERIALIZED VIEW "public"."pec_result_cache" AS WITH languages AS (
         SELECT x.language,
            x.label,
            x.sort_order
           FROM ( VALUES ('python'::text,'Python'::text,1), ('java'::text,'Java'::text,2), ('go'::text,'Go'::text,3), ('javascript'::text,'JavaScript'::text,4), ('cpp'::text,'C++'::text,5), ('cs'::text,'C#'::text,6), ('rust'::text,'Rust'::text,7)) x(language, label, sort_order)
        ), categories AS (
         SELECT x.category,
            x.sort_order,
            x.is_code_category
           FROM ( VALUES ('VAR'::text,1,true), ('TYPE'::text,2,true), ('EXPR'::text,3,true), ('ASSIGN'::text,4,true), ('CTRL'::text,5,true), ('SUBP'::text,6,true), ('OOP'::text,7,false)) x(category, sort_order, is_code_category)
        ), all_data AS (
         SELECT 'python'::text AS language,
            c2t_python.id,
            c2t_python.split,
            c2t_python.pec_data
           FROM c2t_python
          WHERE (c2t_python.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'java'::text AS language,
            c2t_java.id,
            c2t_java.split,
            c2t_java.pec_data
           FROM c2t_java
          WHERE (c2t_java.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'go'::text AS language,
            c2t_go.id,
            c2t_go.split,
            c2t_go.pec_data
           FROM c2t_go
          WHERE (c2t_go.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'javascript'::text AS language,
            c2t_javascript.id,
            c2t_javascript.split,
            c2t_javascript.pec_data
           FROM c2t_javascript
          WHERE (c2t_javascript.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'cpp'::text AS language,
            c2t_cpp.id,
            c2t_cpp.split,
            c2t_cpp.pec_data
           FROM c2t_cpp
          WHERE (c2t_cpp.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'cpp'::text AS language,
            heval_cpp.id,
            heval_cpp.split,
            heval_cpp.pec_data
           FROM heval_cpp
          WHERE (heval_cpp.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'cs'::text AS language,
            c2c_cs.id,
            c2c_cs.split,
            c2c_cs.pec_data
           FROM c2c_cs
          WHERE (c2c_cs.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'cs'::text AS language,
            c2t_cs.id,
            c2t_cs.split,
            c2t_cs.pec_data
           FROM c2t_cs
          WHERE (c2t_cs.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'cs'::text AS language,
            heval.id,
            heval.split,
            heval.pec_data
           FROM heval
          WHERE ((lower((heval.language)::text) = ANY (ARRAY['cs'::text, 'csharp'::text, 'c#'::text])) AND (heval.pec_data IS NOT NULL))
        UNION ALL
         SELECT 'rust'::text AS language,
            c2t_rust.id,
            c2t_rust.split,
            c2t_rust.pec_data
           FROM c2t_rust
          WHERE (c2t_rust.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'rust'::text AS language,
            heval_rust.id,
            heval_rust.split,
            heval_rust.pec_data
           FROM heval_rust
          WHERE (heval_rust.pec_data IS NOT NULL)
        ), category_stats AS (
         SELECT l.language,
            c.category,
            c.sort_order,
            count(d.id) FILTER (WHERE ((d.pec_data -> 'original_all_categories'::text) ? c.category)) AS available_count,
            count(d.id) FILTER (WHERE (((d.pec_data -> 'original_all_categories'::text) ? c.category) AND ((d.pec_data -> 'preserved_all_categories'::text) ? c.category))) AS preserved_count
           FROM ((languages l
             CROSS JOIN categories c)
             LEFT JOIN all_data d ON ((d.language = l.language)))
          GROUP BY l.language, c.category, c.sort_order
        ), category_percent AS (
         SELECT category_stats.language,
            category_stats.category,
            category_stats.sort_order,
            round(
                CASE
                    WHEN (category_stats.available_count = 0) THEN (100)::numeric
                    ELSE (((category_stats.preserved_count)::numeric / (category_stats.available_count)::numeric) * (100)::numeric)
                END, 1) AS pec_percent
           FROM category_stats
        ), pivot_table AS (
         SELECT c.sort_order,
            c.category AS "PEC Category",
            COALESCE(max(
                CASE
                    WHEN (cp.language = 'python'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0) AS "Python",
            COALESCE(max(
                CASE
                    WHEN (cp.language = 'java'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0) AS "Java",
            COALESCE(max(
                CASE
                    WHEN (cp.language = 'go'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0) AS "Go",
            COALESCE(max(
                CASE
                    WHEN (cp.language = 'javascript'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0) AS "JavaScript",
            COALESCE(max(
                CASE
                    WHEN (cp.language = 'cpp'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0) AS "C++",
            COALESCE(max(
                CASE
                    WHEN (cp.language = 'cs'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0) AS "C#",
            COALESCE(max(
                CASE
                    WHEN (cp.language = 'rust'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0) AS "Rust",
            round((((((((COALESCE(max(
                CASE
                    WHEN (cp.language = 'python'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0) + COALESCE(max(
                CASE
                    WHEN (cp.language = 'java'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0)) + COALESCE(max(
                CASE
                    WHEN (cp.language = 'go'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0)) + COALESCE(max(
                CASE
                    WHEN (cp.language = 'javascript'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0)) + COALESCE(max(
                CASE
                    WHEN (cp.language = 'cpp'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0)) + COALESCE(max(
                CASE
                    WHEN (cp.language = 'cs'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0)) + COALESCE(max(
                CASE
                    WHEN (cp.language = 'rust'::text) THEN cp.pec_percent
                    ELSE NULL::numeric
                END), 0.0)) / 7.0), 1) AS "Average"
           FROM (categories c
             LEFT JOIN category_percent cp ON ((cp.category = c.category)))
          GROUP BY c.sort_order, c.category
        ), final_table AS (
         SELECT pivot_table.sort_order,
            pivot_table."PEC Category",
            pivot_table."Python",
            pivot_table."Java",
            pivot_table."Go",
            pivot_table."JavaScript",
            pivot_table."C++",
            pivot_table."C#",
            pivot_table."Rust",
            pivot_table."Average"
           FROM pivot_table
        UNION ALL
         SELECT 8 AS sort_order,
            'AVG PEC ALL'::text AS "PEC Category",
            round(avg(pivot_table."Python"), 1) AS round,
            round(avg(pivot_table."Java"), 1) AS round,
            round(avg(pivot_table."Go"), 1) AS round,
            round(avg(pivot_table."JavaScript"), 1) AS round,
            round(avg(pivot_table."C++"), 1) AS round,
            round(avg(pivot_table."C#"), 1) AS round,
            round(avg(pivot_table."Rust"), 1) AS round,
            round(avg(pivot_table."Average"), 1) AS round
           FROM pivot_table
        UNION ALL
         SELECT 9 AS sort_order,
            'AVG PEC CODE'::text AS "PEC Category",
            round(avg(pivot_table."Python"), 1) AS round,
            round(avg(pivot_table."Java"), 1) AS round,
            round(avg(pivot_table."Go"), 1) AS round,
            round(avg(pivot_table."JavaScript"), 1) AS round,
            round(avg(pivot_table."C++"), 1) AS round,
            round(avg(pivot_table."C#"), 1) AS round,
            round(avg(pivot_table."Rust"), 1) AS round,
            round(avg(pivot_table."Average"), 1) AS round
           FROM pivot_table
          WHERE (pivot_table."PEC Category" <> 'OOP'::text)
        )
 SELECT sort_order,
    "PEC Category",
    "Python",
    "Java",
    "Go",
    "JavaScript",
    "C++",
    "C#",
    "Rust",
    "Average"
   FROM final_table
  ORDER BY sort_order;

DROP TABLE IF EXISTS "pec_result";
DROP VIEW IF EXISTS "pec_result";
CREATE VIEW "public"."pec_result" AS SELECT "PEC Category",
    "Python",
    "Java",
    "Go",
    "JavaScript",
    "C++",
    "C#",
    "Rust",
    "Average"
   FROM pec_result_cache
  ORDER BY sort_order;

DROP TABLE IF EXISTS "statistik_deskriptif";
CREATE VIEW "public"."statistik_deskriptif" AS WITH metric_long AS (
         SELECT 'CodeXGLUE'::text AS dataset,
            'PEC'::text AS metric,
            COALESCE((NULLIF((c2c_cs.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((c2c_cs.pec_data ->> 'pec'::text), ''::text))::numeric, c2c_cs.pec_score) AS value,
            false AS is_percent
           FROM c2c_cs
          WHERE (c2c_cs.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'PEC'::text AS text,
            COALESCE((NULLIF((c2c_java.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((c2c_java.pec_data ->> 'pec'::text), ''::text))::numeric, c2c_java.pec_score) AS "coalesce",
            false AS bool
           FROM c2c_java
          WHERE (c2c_java.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'CLSA'::text AS text,
            c2c_cs.ted,
            false AS bool
           FROM c2c_cs
          WHERE (c2c_cs.ted IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'CLSA'::text AS text,
            c2c_java.ted,
            false AS bool
           FROM c2c_java
          WHERE (c2c_java.ted IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - c2c_cs.compression_ratio),
            false AS bool
           FROM c2c_cs
          WHERE (c2c_cs.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - c2c_java.compression_ratio),
            false AS bool
           FROM c2c_java
          WHERE (c2c_java.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'CO-Time'::text AS text,
            c2c_cs.dtime3,
            true AS bool
           FROM c2c_cs
          WHERE (c2c_cs.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'CO-Time'::text AS text,
            c2c_java.dtime3,
            true AS bool
           FROM c2c_java
          WHERE (c2c_java.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'CO-Mem'::text AS text,
            c2c_cs.dmem3,
            true AS bool
           FROM c2c_cs
          WHERE (c2c_cs.dmem3 IS NOT NULL)
        UNION ALL
         SELECT 'CodeXGLUE'::text AS text,
            'CO-Mem'::text AS text,
            c2c_java.dmem3,
            true AS bool
           FROM c2c_java
          WHERE (c2c_java.dmem3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'PEC'::text AS text,
            COALESCE((NULLIF((heval.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((heval.pec_data ->> 'pec'::text), ''::text))::numeric, heval.pec_score) AS "coalesce",
            false AS bool
           FROM heval
          WHERE (heval.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'PEC'::text AS text,
            COALESCE((NULLIF((heval_cpp.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((heval_cpp.pec_data ->> 'pec'::text), ''::text))::numeric, heval_cpp.pec_score) AS "coalesce",
            false AS bool
           FROM heval_cpp
          WHERE (heval_cpp.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'PEC'::text AS text,
            COALESCE((NULLIF((heval_go.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((heval_go.pec_data ->> 'pec'::text), ''::text))::numeric, heval_go.pec_score) AS "coalesce",
            false AS bool
           FROM heval_go
          WHERE (heval_go.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'PEC'::text AS text,
            COALESCE((NULLIF((heval_java.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((heval_java.pec_data ->> 'pec'::text), ''::text))::numeric, heval_java.pec_score) AS "coalesce",
            false AS bool
           FROM heval_java
          WHERE (heval_java.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'PEC'::text AS text,
            COALESCE((NULLIF((heval_javascript.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((heval_javascript.pec_data ->> 'pec'::text), ''::text))::numeric, heval_javascript.pec_score) AS "coalesce",
            false AS bool
           FROM heval_javascript
          WHERE (heval_javascript.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'PEC'::text AS text,
            COALESCE((NULLIF((heval_python.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((heval_python.pec_data ->> 'pec'::text), ''::text))::numeric, heval_python.pec_score) AS "coalesce",
            false AS bool
           FROM heval_python
          WHERE (heval_python.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'PEC'::text AS text,
            COALESCE((NULLIF((heval_rust.pec_data ->> 'pec_code'::text), ''::text))::numeric, (NULLIF((heval_rust.pec_data ->> 'pec'::text), ''::text))::numeric, heval_rust.pec_score) AS "coalesce",
            false AS bool
           FROM heval_rust
          WHERE (heval_rust.pec_data IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CLSA'::text AS text,
            heval_matrix.ted,
            false AS bool
           FROM heval_matrix
          WHERE (heval_matrix.ted IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - heval.compression_ratio),
            false AS bool
           FROM heval
          WHERE (heval.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - heval_cpp.compression_ratio),
            false AS bool
           FROM heval_cpp
          WHERE (heval_cpp.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - heval_go.compression_ratio),
            false AS bool
           FROM heval_go
          WHERE (heval_go.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - heval_java.compression_ratio),
            false AS bool
           FROM heval_java
          WHERE (heval_java.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - heval_javascript.compression_ratio),
            false AS bool
           FROM heval_javascript
          WHERE (heval_javascript.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - heval_python.compression_ratio),
            false AS bool
           FROM heval_python
          WHERE (heval_python.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'RESR'::text AS text,
            ((1)::numeric - heval_rust.compression_ratio),
            false AS bool
           FROM heval_rust
          WHERE (heval_rust.compression_ratio IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Time'::text AS text,
            heval.dtime3,
            true AS bool
           FROM heval
          WHERE (heval.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Time'::text AS text,
            heval_cpp.dtime3,
            true AS bool
           FROM heval_cpp
          WHERE (heval_cpp.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Time'::text AS text,
            heval_go.dtime3,
            true AS bool
           FROM heval_go
          WHERE (heval_go.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Time'::text AS text,
            heval_java.dtime3,
            true AS bool
           FROM heval_java
          WHERE (heval_java.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Time'::text AS text,
            heval_javascript.dtime3,
            true AS bool
           FROM heval_javascript
          WHERE (heval_javascript.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Time'::text AS text,
            heval_python.dtime3,
            true AS bool
           FROM heval_python
          WHERE (heval_python.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Time'::text AS text,
            heval_rust.dtime3,
            true AS bool
           FROM heval_rust
          WHERE (heval_rust.dtime3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Mem'::text AS text,
            heval.dmem3,
            true AS bool
           FROM heval
          WHERE (heval.dmem3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Mem'::text AS text,
            heval_cpp.dmem3,
            true AS bool
           FROM heval_cpp
          WHERE (heval_cpp.dmem3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Mem'::text AS text,
            heval_go.dmem3,
            true AS bool
           FROM heval_go
          WHERE (heval_go.dmem3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Mem'::text AS text,
            heval_java.dmem3,
            true AS bool
           FROM heval_java
          WHERE (heval_java.dmem3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Mem'::text AS text,
            heval_javascript.dmem3,
            true AS bool
           FROM heval_javascript
          WHERE (heval_javascript.dmem3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Mem'::text AS text,
            heval_python.dmem3,
            true AS bool
           FROM heval_python
          WHERE (heval_python.dmem3 IS NOT NULL)
        UNION ALL
         SELECT 'HumanEval'::text AS text,
            'CO-Mem'::text AS text,
            heval_rust.dmem3,
            true AS bool
           FROM heval_rust
          WHERE (heval_rust.dmem3 IS NOT NULL)
        ), summary_table AS (
         SELECT metric_long.dataset,
            metric_long.metric,
            metric_long.is_percent,
            avg(metric_long.value) AS mean_value,
            stddev_samp(metric_long.value) AS std_dev_value,
            min(metric_long.value) AS min_value,
            max(metric_long.value) AS max_value
           FROM metric_long
          WHERE (metric_long.value IS NOT NULL)
          GROUP BY metric_long.dataset, metric_long.metric, metric_long.is_percent
        )
 SELECT dataset AS "Dataset",
    metric AS "Metrik",
        CASE
            WHEN is_percent THEN ((round(mean_value, 3))::text || '%'::text)
            ELSE (round(mean_value, 3))::text
        END AS "Mean",
        CASE
            WHEN is_percent THEN ((round(std_dev_value, 3))::text || '%'::text)
            ELSE (round(std_dev_value, 3))::text
        END AS "Std. Dev.",
        CASE
            WHEN is_percent THEN ((round(min_value, 3))::text || '%'::text)
            ELSE (round(min_value, 3))::text
        END AS "Min",
        CASE
            WHEN is_percent THEN ((round(max_value, 3))::text || '%'::text)
            ELSE (round(max_value, 3))::text
        END AS "Max"
   FROM summary_table
  ORDER BY
        CASE dataset
            WHEN 'CodeXGLUE'::text THEN 1
            WHEN 'HumanEval'::text THEN 2
            ELSE 3
        END,
        CASE metric
            WHEN 'PEC'::text THEN 1
            WHEN 'CLSA'::text THEN 2
            WHEN 'RESR'::text THEN 3
            WHEN 'CO-Time'::text THEN 4
            WHEN 'CO-Mem'::text THEN 5
            ELSE 6
        END;

DROP TABLE IF EXISTS "v_c2c_metrics";
CREATE VIEW "public"."v_c2c_metrics" AS WITH all_data AS (
         SELECT 'cs'::text AS language1,
            'java'::text AS language2,
            c2c_cs.ted,
            c2c_cs.ted2,
            c2c_cs.ted3,
            c2c_cs.ted4,
            c2c_cs.similarity,
            c2c_cs.reconstruction_bleu,
            c2c_cs.compression_ratio,
            c2c_cs.f1,
            c2c_cs."precision",
            c2c_cs.recall,
            c2c_cs.dmem3,
            c2c_cs.dtime3,
            c2c_cs.attribut_loss,
            c2c_cs.pec_score,
            c2c_cs.pec_score_all
           FROM c2c_cs
        UNION ALL
         SELECT 'java'::text AS language1,
            'cs'::text AS language2,
            c2c_java.ted,
            c2c_java.ted2,
            c2c_java.ted3,
            c2c_java.ted4,
            c2c_java.similarity,
            c2c_java.reconstruction_bleu,
            c2c_java.compression_ratio,
            c2c_java.f1,
            c2c_java."precision",
            c2c_java.recall,
            c2c_java.dmem3,
            c2c_java.dtime3,
            c2c_java.attribut_loss,
            c2c_java.pec_score,
            c2c_java.pec_score_all
           FROM c2c_java
        )
 SELECT language1,
    language2,
    round(avg(ted), 2) AS ted_uast_uast_mean,
    round(stddev_samp(ted), 2) AS ted_uast_uast_std_dev,
    round(min(ted), 2) AS ted_uast_uast_min,
    round(max(ted), 2) AS ted_uast_uast_max,
    round(avg(ted2), 2) AS ted_uast_original_mean,
    round(stddev_samp(ted2), 2) AS ted_uast_original_std_dev,
    round(min(ted2), 2) AS ted_uast_original_min,
    round(max(ted2), 2) AS ted_uast_original_max,
    round(avg(ted3), 2) AS ted_original_uast_mean,
    round(stddev_samp(ted3), 2) AS ted_original_uast_std_dev,
    round(min(ted3), 2) AS ted_original_uast_min,
    round(max(ted3), 2) AS ted_original_uast_max,
    round(avg(ted4), 2) AS ted_original_original_mean,
    round(stddev_samp(ted4), 2) AS ted_original_original_std_dev,
    round(min(ted4), 2) AS ted_original_original_min,
    round(max(ted4), 2) AS ted_original_original_max,
    round(avg(similarity), 2) AS cosine_similarity_mean,
    round(stddev_samp(similarity), 2) AS cosine_similarity_std_dev,
    round(min(similarity), 2) AS cosine_similarity_min,
    round(max(similarity), 2) AS cosine_similarity_max,
    round(avg(reconstruction_bleu), 2) AS reconstruction_bleu_mean,
    round(stddev_samp(reconstruction_bleu), 2) AS reconstruction_bleu_std_dev,
    round(min(reconstruction_bleu), 2) AS reconstruction_bleu_min,
    round(max(reconstruction_bleu), 2) AS reconstruction_bleu_max,
    round(avg(compression_ratio), 2) AS compression_ratio_mean,
    round(stddev_samp(compression_ratio), 2) AS compression_ratio_std_dev,
    round(min(compression_ratio), 2) AS compression_ratio_min,
    round(max(compression_ratio), 2) AS compression_ratio_max,
    round(avg(f1), 5) AS f1_mean,
    round(stddev_samp(f1), 5) AS f1_std_dev,
    round(min(f1), 5) AS f1_min,
    round(max(f1), 5) AS f1_max,
    round(avg("precision"), 5) AS precision_mean,
    round(stddev_samp("precision"), 5) AS precision_std_dev,
    round(min("precision"), 5) AS precision_min,
    round(max("precision"), 5) AS precision_max,
    round(avg(recall), 5) AS recall_mean,
    round(stddev_samp(recall), 5) AS recall_std_dev,
    round(min(recall), 5) AS recall_min,
    round(max(recall), 5) AS recall_max,
    round(avg(dmem3), 5) AS dmem_mean,
    round(stddev_samp(dmem3), 5) AS dmem_std_dev,
    round(min(dmem3), 5) AS dmem_min,
    round(max(dmem3), 5) AS dmem_max,
    round(avg(dtime3), 5) AS dtime_mean,
    round(stddev_samp(dtime3), 5) AS dtime_std_dev,
    round(min(dtime3), 5) AS dtime_min,
    round(max(dtime3), 5) AS dtime_max,
    round(avg(attribut_loss), 5) AS attribut_loss_mean,
    round(stddev_samp(attribut_loss), 5) AS attribut_loss_std_dev,
    round(min(attribut_loss), 5) AS attribut_loss_min,
    round(max(attribut_loss), 5) AS attribut_loss_max,
    round(avg(pec_score), 2) AS pec_score_mean,
    round(stddev_samp(pec_score), 2) AS pec_score_std_dev,
    round(min(pec_score), 2) AS pec_score_min,
    round(max(pec_score), 2) AS pec_score_max,
    round(avg(pec_score_all), 2) AS pec_score_all_mean,
    round(stddev_samp(pec_score_all), 2) AS pec_score_all_std_dev,
    round(min(pec_score_all), 2) AS pec_score_all_min,
    round(max(pec_score_all), 2) AS pec_score_all_max
   FROM all_data
  GROUP BY language1, language2
  ORDER BY language1, language2;

DROP TABLE IF EXISTS "v_humaneval_metrics";
CREATE VIEW "public"."v_humaneval_metrics" AS SELECT 'cpp'::text AS language,
    round(avg(heval_cpp.similarity), 5) AS cosine_similarity,
    round(avg(heval_cpp.compression_ratio), 5) AS compression_ratio,
    round(avg(heval_cpp.reconstruction_bleu), 5) AS reconstruction_bleu,
    round(avg(heval_cpp.f1), 5) AS f1,
    round(avg(heval_cpp."precision"), 5) AS "precision",
    round(avg(heval_cpp.recall), 5) AS recall,
    round((avg(heval_cpp.dtime) * (1000)::numeric), 5) AS ast_time_ms,
    round((avg(heval_cpp.dtime1) * (1000)::numeric), 5) AS total_time_ms,
    round((avg(heval_cpp.dtime2) * (1000)::numeric), 5) AS uast_extra_time_ms,
    round(((avg(heval_cpp.dmem) / 1024.0) / 1024.0), 5) AS ast_memory_mb,
    round(((avg(heval_cpp.dmem1) / 1024.0) / 1024.0), 5) AS total_memory_mb,
    round(((avg(heval_cpp.dmem2) / 1024.0) / 1024.0), 5) AS uast_extra_memory_mb,
    round(avg(heval_cpp.dtime3), 5) AS time_overhead_percent,
    round(avg(heval_cpp.dmem3), 5) AS memory_overhead_percent,
    round(avg(heval_cpp.attribut_loss), 5) AS attribut_loss
   FROM heval_cpp
UNION ALL
 SELECT 'go'::text AS language,
    round(avg(heval_go.similarity), 5) AS cosine_similarity,
    round(avg(heval_go.compression_ratio), 5) AS compression_ratio,
    round(avg(heval_go.reconstruction_bleu), 5) AS reconstruction_bleu,
    round(avg(heval_go.f1), 5) AS f1,
    round(avg(heval_go."precision"), 5) AS "precision",
    round(avg(heval_go.recall), 5) AS recall,
    round((avg(heval_go.dtime) * (1000)::numeric), 5) AS ast_time_ms,
    round((avg(heval_go.dtime1) * (1000)::numeric), 5) AS total_time_ms,
    round((avg(heval_go.dtime2) * (1000)::numeric), 5) AS uast_extra_time_ms,
    round(((avg(heval_go.dmem) / 1024.0) / 1024.0), 5) AS ast_memory_mb,
    round(((avg(heval_go.dmem1) / 1024.0) / 1024.0), 5) AS total_memory_mb,
    round(((avg(heval_go.dmem2) / 1024.0) / 1024.0), 5) AS uast_extra_memory_mb,
    round(avg(heval_go.dtime3), 5) AS time_overhead_percent,
    round(avg(heval_go.dmem3), 5) AS memory_overhead_percent,
    round(avg(heval_go.attribut_loss), 5) AS attribut_loss
   FROM heval_go
UNION ALL
 SELECT 'java'::text AS language,
    round(avg(heval_java.similarity), 5) AS cosine_similarity,
    round(avg(heval_java.compression_ratio), 5) AS compression_ratio,
    round(avg(heval_java.reconstruction_bleu), 5) AS reconstruction_bleu,
    round(avg(heval_java.f1), 5) AS f1,
    round(avg(heval_java."precision"), 5) AS "precision",
    round(avg(heval_java.recall), 5) AS recall,
    round((avg(heval_java.dtime) * (1000)::numeric), 5) AS ast_time_ms,
    round((avg(heval_java.dtime1) * (1000)::numeric), 5) AS total_time_ms,
    round((avg(heval_java.dtime2) * (1000)::numeric), 5) AS uast_extra_time_ms,
    round(((avg(heval_java.dmem) / 1024.0) / 1024.0), 5) AS ast_memory_mb,
    round(((avg(heval_java.dmem1) / 1024.0) / 1024.0), 5) AS total_memory_mb,
    round(((avg(heval_java.dmem2) / 1024.0) / 1024.0), 5) AS uast_extra_memory_mb,
    round(avg(heval_java.dtime3), 5) AS time_overhead_percent,
    round(avg(heval_java.dmem3), 5) AS memory_overhead_percent,
    round(avg(heval_java.attribut_loss), 5) AS attribut_loss
   FROM heval_java
UNION ALL
 SELECT 'javascript'::text AS language,
    round(avg(heval_javascript.similarity), 5) AS cosine_similarity,
    round(avg(heval_javascript.compression_ratio), 5) AS compression_ratio,
    round(avg(heval_javascript.reconstruction_bleu), 5) AS reconstruction_bleu,
    round(avg(heval_javascript.f1), 5) AS f1,
    round(avg(heval_javascript."precision"), 5) AS "precision",
    round(avg(heval_javascript.recall), 5) AS recall,
    round((avg(heval_javascript.dtime) * (1000)::numeric), 5) AS ast_time_ms,
    round((avg(heval_javascript.dtime1) * (1000)::numeric), 5) AS total_time_ms,
    round((avg(heval_javascript.dtime2) * (1000)::numeric), 5) AS uast_extra_time_ms,
    round(((avg(heval_javascript.dmem) / 1024.0) / 1024.0), 5) AS ast_memory_mb,
    round(((avg(heval_javascript.dmem1) / 1024.0) / 1024.0), 5) AS total_memory_mb,
    round(((avg(heval_javascript.dmem2) / 1024.0) / 1024.0), 5) AS uast_extra_memory_mb,
    round(avg(heval_javascript.dtime3), 5) AS time_overhead_percent,
    round(avg(heval_javascript.dmem3), 5) AS memory_overhead_percent,
    round(avg(heval_javascript.attribut_loss), 5) AS attribut_loss
   FROM heval_javascript
UNION ALL
 SELECT 'python'::text AS language,
    round(avg(heval_python.similarity), 5) AS cosine_similarity,
    round(avg(heval_python.compression_ratio), 5) AS compression_ratio,
    round(avg(heval_python.reconstruction_bleu), 5) AS reconstruction_bleu,
    round(avg(heval_python.f1), 5) AS f1,
    round(avg(heval_python."precision"), 5) AS "precision",
    round(avg(heval_python.recall), 5) AS recall,
    round((avg(heval_python.dtime) * (1000)::numeric), 5) AS ast_time_ms,
    round((avg(heval_python.dtime1) * (1000)::numeric), 5) AS total_time_ms,
    round((avg(heval_python.dtime2) * (1000)::numeric), 5) AS uast_extra_time_ms,
    round(((avg(heval_python.dmem) / 1024.0) / 1024.0), 5) AS ast_memory_mb,
    round(((avg(heval_python.dmem1) / 1024.0) / 1024.0), 5) AS total_memory_mb,
    round(((avg(heval_python.dmem2) / 1024.0) / 1024.0), 5) AS uast_extra_memory_mb,
    round(avg(heval_python.dtime3), 5) AS time_overhead_percent,
    round(avg(heval_python.dmem3), 5) AS memory_overhead_percent,
    round(avg(heval_python.attribut_loss), 5) AS attribut_loss
   FROM heval_python
UNION ALL
 SELECT 'rust'::text AS language,
    round(avg(heval_rust.similarity), 5) AS cosine_similarity,
    round(avg(heval_rust.compression_ratio), 5) AS compression_ratio,
    round(avg(heval_rust.reconstruction_bleu), 5) AS reconstruction_bleu,
    round(avg(heval_rust.f1), 5) AS f1,
    round(avg(heval_rust."precision"), 5) AS "precision",
    round(avg(heval_rust.recall), 5) AS recall,
    round((avg(heval_rust.dtime) * (1000)::numeric), 5) AS ast_time_ms,
    round((avg(heval_rust.dtime1) * (1000)::numeric), 5) AS total_time_ms,
    round((avg(heval_rust.dtime2) * (1000)::numeric), 5) AS uast_extra_time_ms,
    round(((avg(heval_rust.dmem) / 1024.0) / 1024.0), 5) AS ast_memory_mb,
    round(((avg(heval_rust.dmem1) / 1024.0) / 1024.0), 5) AS total_memory_mb,
    round(((avg(heval_rust.dmem2) / 1024.0) / 1024.0), 5) AS uast_extra_memory_mb,
    round(avg(heval_rust.dtime3), 5) AS time_overhead_percent,
    round(avg(heval_rust.dmem3), 5) AS memory_overhead_percent,
    round(avg(heval_rust.attribut_loss), 5) AS attribut_loss
   FROM heval_rust;

DROP TABLE IF EXISTS "vstat_c2c";
CREATE VIEW "public"."vstat_c2c" AS WITH all_data AS (
         SELECT 'cs'::text AS language1,
            'java'::text AS language2,
            c2c_cs.ted,
            c2c_cs.ted2,
            c2c_cs.ted3,
            c2c_cs.ted4,
            c2c_cs.similarity,
            c2c_cs.reconstruction_bleu,
            c2c_cs.compression_ratio,
            c2c_cs.f1,
            c2c_cs."precision",
            c2c_cs.recall,
            c2c_cs.dmem3,
            c2c_cs.dtime3,
            c2c_cs.attribut_loss,
            c2c_cs.pec_score,
            c2c_cs.pec_score_all
           FROM c2c_cs
        UNION ALL
         SELECT 'java'::text AS language1,
            'cs'::text AS language2,
            c2c_java.ted,
            c2c_java.ted2,
            c2c_java.ted3,
            c2c_java.ted4,
            c2c_java.similarity,
            c2c_java.reconstruction_bleu,
            c2c_java.compression_ratio,
            c2c_java.f1,
            c2c_java."precision",
            c2c_java.recall,
            c2c_java.dmem3,
            c2c_java.dtime3,
            c2c_java.attribut_loss,
            c2c_java.pec_score,
            c2c_java.pec_score_all
           FROM c2c_java
        )
 SELECT language1,
    language2,
    round(avg(ted), 2) AS ted_uast_uast_mean,
    round(stddev_samp(ted), 2) AS ted_uast_uast_std_dev,
    round(min(ted), 2) AS ted_uast_uast_min,
    round(max(ted), 2) AS ted_uast_uast_max,
    round(avg(ted2), 2) AS ted_uast_original_mean,
    round(stddev_samp(ted2), 2) AS ted_uast_original_std_dev,
    round(min(ted2), 2) AS ted_uast_original_min,
    round(max(ted2), 2) AS ted_uast_original_max,
    round(avg(ted3), 2) AS ted_original_uast_mean,
    round(stddev_samp(ted3), 2) AS ted_original_uast_std_dev,
    round(min(ted3), 2) AS ted_original_uast_min,
    round(max(ted3), 2) AS ted_original_uast_max,
    round(avg(ted4), 2) AS ted_original_original_mean,
    round(stddev_samp(ted4), 2) AS ted_original_original_std_dev,
    round(min(ted4), 2) AS ted_original_original_min,
    round(max(ted4), 2) AS ted_original_original_max,
    round(avg(similarity), 2) AS cosine_similarity_mean,
    round(stddev_samp(similarity), 2) AS cosine_similarity_std_dev,
    round(min(similarity), 2) AS cosine_similarity_min,
    round(max(similarity), 2) AS cosine_similarity_max,
    round(avg(reconstruction_bleu), 2) AS reconstruction_bleu_mean,
    round(stddev_samp(reconstruction_bleu), 2) AS reconstruction_bleu_std_dev,
    round(min(reconstruction_bleu), 2) AS reconstruction_bleu_min,
    round(max(reconstruction_bleu), 2) AS reconstruction_bleu_max,
    round(avg(compression_ratio), 2) AS compression_ratio_mean,
    round(stddev_samp(compression_ratio), 2) AS compression_ratio_std_dev,
    round(min(compression_ratio), 2) AS compression_ratio_min,
    round(max(compression_ratio), 2) AS compression_ratio_max,
    round(avg(f1), 5) AS f1_mean,
    round(stddev_samp(f1), 5) AS f1_std_dev,
    round(min(f1), 5) AS f1_min,
    round(max(f1), 5) AS f1_max,
    round(avg("precision"), 5) AS precision_mean,
    round(stddev_samp("precision"), 5) AS precision_std_dev,
    round(min("precision"), 5) AS precision_min,
    round(max("precision"), 5) AS precision_max,
    round(avg(recall), 5) AS recall_mean,
    round(stddev_samp(recall), 5) AS recall_std_dev,
    round(min(recall), 5) AS recall_min,
    round(max(recall), 5) AS recall_max,
    round(avg(dmem3), 5) AS dmem_mean,
    round(stddev_samp(dmem3), 5) AS dmem_std_dev,
    round(min(dmem3), 5) AS dmem_min,
    round(max(dmem3), 5) AS dmem_max,
    round(avg(dtime3), 5) AS dtime_mean,
    round(stddev_samp(dtime3), 5) AS dtime_std_dev,
    round(min(dtime3), 5) AS dtime_min,
    round(max(dtime3), 5) AS dtime_max,
    round(avg(attribut_loss), 5) AS attribut_loss_mean,
    round(stddev_samp(attribut_loss), 5) AS attribut_loss_std_dev,
    round(min(attribut_loss), 5) AS attribut_loss_min,
    round(max(attribut_loss), 5) AS attribut_loss_max,
    round(avg(pec_score), 2) AS pec_score_mean,
    round(stddev_samp(pec_score), 2) AS pec_score_std_dev,
    round(min(pec_score), 2) AS pec_score_min,
    round(max(pec_score), 2) AS pec_score_max,
    round(avg(pec_score_all), 2) AS pec_score_all_mean,
    round(stddev_samp(pec_score_all), 2) AS pec_score_all_std_dev,
    round(min(pec_score_all), 2) AS pec_score_all_min,
    round(max(pec_score_all), 2) AS pec_score_all_max
   FROM all_data
  GROUP BY language1, language2
  ORDER BY language1, language2;

DROP TABLE IF EXISTS "vstat_c2t";
CREATE VIEW "public"."vstat_c2t" AS SELECT 'go'::text AS language,
    round(avg(c2t_go.compression_ratio), 5) AS compression_ratio,
    round(avg(c2t_go.reconstruction_bleu), 5) AS bleu,
    round(avg(c2t_go.f1), 5) AS f1,
    round(avg(c2t_go."precision"), 5) AS "precision",
    round(avg(c2t_go.recall), 5) AS recall,
    round(avg(c2t_go.dmem3), 5) AS dmem,
    round(avg(c2t_go.dtime3), 5) AS dtime,
    round(avg(c2t_go.attribut_loss), 5) AS attribut_loss
   FROM c2t_go
UNION ALL
 SELECT 'java'::text AS language,
    round(avg(c2t_java.compression_ratio), 5) AS compression_ratio,
    round(avg(c2t_java.reconstruction_bleu), 5) AS bleu,
    round(avg(c2t_java.f1), 5) AS f1,
    round(avg(c2t_java."precision"), 5) AS "precision",
    round(avg(c2t_java.recall), 5) AS recall,
    round(avg(c2t_java.dmem3), 5) AS dmem,
    round(avg(c2t_java.dtime3), 5) AS dtime,
    round(avg(c2t_java.attribut_loss), 5) AS attribut_loss
   FROM c2t_java
UNION ALL
 SELECT 'javascript'::text AS language,
    round(avg(c2t_javascript.compression_ratio), 5) AS compression_ratio,
    round(avg(c2t_javascript.reconstruction_bleu), 5) AS bleu,
    round(avg(c2t_javascript.f1), 5) AS f1,
    round(avg(c2t_javascript."precision"), 5) AS "precision",
    round(avg(c2t_javascript.recall), 5) AS recall,
    round(avg(c2t_javascript.dmem3), 5) AS dmem,
    round(avg(c2t_javascript.dtime3), 5) AS dtime,
    round(avg(c2t_javascript.attribut_loss), 5) AS attribut_loss
   FROM c2t_javascript
UNION ALL
 SELECT 'php'::text AS language,
    round(avg(c2t_php.compression_ratio), 5) AS compression_ratio,
    round(avg(c2t_php.reconstruction_bleu), 5) AS bleu,
    round(avg(c2t_php.f1), 5) AS f1,
    round(avg(c2t_php."precision"), 5) AS "precision",
    round(avg(c2t_php.recall), 5) AS recall,
    round(avg(c2t_php.dmem3), 5) AS dmem,
    round(avg(c2t_php.dtime3), 5) AS dtime,
    round(avg(c2t_php.attribut_loss), 5) AS attribut_loss
   FROM c2t_php
UNION ALL
 SELECT 'python'::text AS language,
    round(avg(c2t_python.compression_ratio), 5) AS compression_ratio,
    round(avg(c2t_python.reconstruction_bleu), 5) AS bleu,
    round(avg(c2t_python.f1), 5) AS f1,
    round(avg(c2t_python."precision"), 5) AS "precision",
    round(avg(c2t_python.recall), 5) AS recall,
    round(avg(c2t_python.dmem3), 5) AS dmem,
    round(avg(c2t_python.dtime3), 5) AS dtime,
    round(avg(c2t_python.attribut_loss), 5) AS attribut_loss
   FROM c2t_python
UNION ALL
 SELECT 'ruby'::text AS language,
    round(avg(c2t_ruby.compression_ratio), 5) AS compression_ratio,
    round(avg(c2t_ruby.reconstruction_bleu), 5) AS bleu,
    round(avg(c2t_ruby.f1), 5) AS f1,
    round(avg(c2t_ruby."precision"), 5) AS "precision",
    round(avg(c2t_ruby.recall), 5) AS recall,
    round(avg(c2t_ruby.dmem3), 5) AS dmem,
    round(avg(c2t_ruby.dtime3), 5) AS dtime,
    round(avg(c2t_ruby.attribut_loss), 5) AS attribut_loss
   FROM c2t_ruby;

DROP TABLE IF EXISTS "vstat_heval";
CREATE VIEW "public"."vstat_heval" AS WITH all_data AS (
         SELECT 'cpp'::text AS language,
            heval_cpp.similarity,
            heval_cpp.compression_ratio,
            heval_cpp.reconstruction_bleu,
            heval_cpp.f1,
            heval_cpp."precision",
            heval_cpp.recall,
            heval_cpp.dmem3,
            heval_cpp.dtime3,
            heval_cpp.attribut_loss,
            heval_cpp.pec_score,
            heval_cpp.pec_score_all
           FROM heval_cpp
        UNION ALL
         SELECT 'go'::text AS language,
            heval_go.similarity,
            heval_go.compression_ratio,
            heval_go.reconstruction_bleu,
            heval_go.f1,
            heval_go."precision",
            heval_go.recall,
            heval_go.dmem3,
            heval_go.dtime3,
            heval_go.attribut_loss,
            heval_go.pec_score,
            heval_go.pec_score_all
           FROM heval_go
        UNION ALL
         SELECT 'java'::text AS language,
            heval_java.similarity,
            heval_java.compression_ratio,
            heval_java.reconstruction_bleu,
            heval_java.f1,
            heval_java."precision",
            heval_java.recall,
            heval_java.dmem3,
            heval_java.dtime3,
            heval_java.attribut_loss,
            heval_java.pec_score,
            heval_java.pec_score_all
           FROM heval_java
        UNION ALL
         SELECT 'javascript'::text AS language,
            heval_javascript.similarity,
            heval_javascript.compression_ratio,
            heval_javascript.reconstruction_bleu,
            heval_javascript.f1,
            heval_javascript."precision",
            heval_javascript.recall,
            heval_javascript.dmem3,
            heval_javascript.dtime3,
            heval_javascript.attribut_loss,
            heval_javascript.pec_score,
            heval_javascript.pec_score_all
           FROM heval_javascript
        UNION ALL
         SELECT 'python'::text AS language,
            heval_python.similarity,
            heval_python.compression_ratio,
            heval_python.reconstruction_bleu,
            heval_python.f1,
            heval_python."precision",
            heval_python.recall,
            heval_python.dmem3,
            heval_python.dtime3,
            heval_python.attribut_loss,
            heval_python.pec_score,
            heval_python.pec_score_all
           FROM heval_python
        UNION ALL
         SELECT 'rust'::text AS language,
            heval_rust.similarity,
            heval_rust.compression_ratio,
            heval_rust.reconstruction_bleu,
            heval_rust.f1,
            heval_rust."precision",
            heval_rust.recall,
            heval_rust.dmem3,
            heval_rust.dtime3,
            heval_rust.attribut_loss,
            heval_rust.pec_score,
            heval_rust.pec_score_all
           FROM heval_rust
        )
 SELECT language,
    round(avg(similarity), 5) AS cosine_similarity_mean,
    round(stddev_samp(similarity), 5) AS cosine_similarity_std_dev,
    round(min(similarity), 5) AS cosine_similarity_min,
    round(max(similarity), 5) AS cosine_similarity_max,
    round(avg(compression_ratio), 5) AS compression_ratio_mean,
    round(stddev_samp(compression_ratio), 5) AS compression_ratio_std_dev,
    round(min(compression_ratio), 5) AS compression_ratio_min,
    round(max(compression_ratio), 5) AS compression_ratio_max,
    round(avg(reconstruction_bleu), 5) AS reconstruction_bleu_mean,
    round(stddev_samp(reconstruction_bleu), 5) AS reconstruction_bleu_std_dev,
    round(min(reconstruction_bleu), 5) AS reconstruction_bleu_min,
    round(max(reconstruction_bleu), 5) AS reconstruction_bleu_max,
    round(avg(f1), 5) AS f1_mean,
    round(stddev_samp(f1), 5) AS f1_std_dev,
    round(min(f1), 5) AS f1_min,
    round(max(f1), 5) AS f1_max,
    round(avg("precision"), 5) AS precision_mean,
    round(stddev_samp("precision"), 5) AS precision_std_dev,
    round(min("precision"), 5) AS precision_min,
    round(max("precision"), 5) AS precision_max,
    round(avg(recall), 5) AS recall_mean,
    round(stddev_samp(recall), 5) AS recall_std_dev,
    round(min(recall), 5) AS recall_min,
    round(max(recall), 5) AS recall_max,
    round(avg(dmem3), 5) AS dmem_mean,
    round(stddev_samp(dmem3), 5) AS dmem_std_dev,
    round(min(dmem3), 5) AS dmem_min,
    round(max(dmem3), 5) AS dmem_max,
    round(avg(dtime3), 5) AS dtime_mean,
    round(stddev_samp(dtime3), 5) AS dtime_std_dev,
    round(min(dtime3), 5) AS dtime_min,
    round(max(dtime3), 5) AS dtime_max,
    round(avg(attribut_loss), 5) AS attribut_loss_mean,
    round(stddev_samp(attribut_loss), 5) AS attribut_loss_std_dev,
    round(min(attribut_loss), 5) AS attribut_loss_min,
    round(max(attribut_loss), 5) AS attribut_loss_max,
    round(avg(pec_score), 5) AS pec_score_mean,
    round(stddev_samp(pec_score), 5) AS pec_score_std_dev,
    round(min(pec_score), 5) AS pec_score_min,
    round(max(pec_score), 5) AS pec_score_max,
    round(avg(pec_score_all), 5) AS pec_score_all_mean,
    round(stddev_samp(pec_score_all), 5) AS pec_score_all_std_dev,
    round(min(pec_score_all), 5) AS pec_score_all_min,
    round(max(pec_score_all), 5) AS pec_score_all_max
   FROM all_data
  GROUP BY language
  ORDER BY language;

DROP TABLE IF EXISTS "vted_heval";
CREATE VIEW "public"."vted_heval" AS SELECT language1,
    language2,
    round(avg(ted), 2) AS ted_uast_uast_mean,
    round(stddev_samp(ted), 2) AS ted_uast_uast_std_dev,
    round(min(ted), 2) AS ted_uast_uast_min,
    round(max(ted), 2) AS ted_uast_uast_max,
    round(avg(ted2), 2) AS ted_uast_original_mean,
    round(stddev_samp(ted2), 2) AS ted_uast_original_std_dev,
    round(min(ted2), 2) AS ted_uast_original_min,
    round(max(ted2), 2) AS ted_uast_original_max,
    round(avg(ted3), 2) AS ted_original_uast_mean,
    round(stddev_samp(ted3), 2) AS ted_original_uast_std_dev,
    round(min(ted3), 2) AS ted_original_uast_min,
    round(max(ted3), 2) AS ted_original_uast_max,
    round(avg(ted4), 2) AS ted_original_original_mean,
    round(stddev_samp(ted4), 2) AS ted_original_original_std_dev,
    round(min(ted4), 2) AS ted_original_original_min,
    round(max(ted4), 2) AS ted_original_original_max,
    round(avg(similarity), 2) AS cosine_similarity_mean,
    round(stddev_samp(similarity), 2) AS cosine_similarity_std_dev,
    round(min(similarity), 2) AS cosine_similarity_min,
    round(max(similarity), 2) AS cosine_similarity_max
   FROM heval_matrix
  GROUP BY language1, language2;

-- 2026-06-18 21:22:46 UTC

-- ============================================================
-- Audit & Experiment Tables (merged from 11_revision_schema.sql)
-- REV-R1.7/R2.2/R2.4/R2.6
-- ============================================================

CREATE TABLE IF NOT EXISTS experiment_run_metadata (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    script_name text NOT NULL,
    dataset text,
    config jsonb,
    environment jsonb,
    notes text
);

CREATE TABLE IF NOT EXISTS raw_measurement_audit (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    dataset text NOT NULL,
    table_name text NOT NULL,
    language text,
    split text,
    row_id bigint,
    code_sha256 text,
    ast_sha256 text,
    uast_sha256 text,
    summary jsonb,
    raw_runs jsonb
);

CREATE TABLE IF NOT EXISTS baseline_comparison_results (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    dataset text NOT NULL,
    baseline_name text NOT NULL,
    language1 text,
    language2 text,
    sample_count integer,
    pec_core numeric,
    pec_all numeric,
    clsa numeric,
    resr numeric,
    code_similarity numeric,
    details jsonb
);

CREATE TABLE IF NOT EXISTS dataset_artifact_hashes (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    artifact_type text NOT NULL,
    artifact_name text NOT NULL,
    artifact_path text NOT NULL,
    sha256 text NOT NULL,
    file_count integer,
    total_bytes bigint,
    details jsonb
);

CREATE TABLE IF NOT EXISTS intrinsic_sensitivity_results (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    dataset text NOT NULL,
    task text NOT NULL,
    metric text NOT NULL,
    language1 text,
    language2 text,
    sample_key text NOT NULL,
    representation text NOT NULL,
    corruption_type text NOT NULL,
    corruption_level numeric NOT NULL,
    sample_count integer,
    baseline_value numeric,
    value numeric NOT NULL,
    delta numeric,
    details jsonb
);

CREATE TABLE IF NOT EXISTS stagewise_ablation_results (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    dataset text NOT NULL,
    ablation_variant text NOT NULL,
    stage_order integer NOT NULL,
    sample_count integer,
    pair_count integer,
    pec_core numeric,
    pec_all numeric,
    clsa numeric,
    resr numeric,
    avg_nodes numeric,
    details jsonb
);

CREATE TABLE IF NOT EXISTS downstream_correlation_results (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    dataset text NOT NULL,
    intrinsic_metric text NOT NULL,
    downstream_metric text NOT NULL,
    sample_count integer,
    pearson_r numeric,
    spearman_r numeric,
    ci95_low numeric,
    ci95_high numeric,
    details jsonb
);

CREATE TABLE IF NOT EXISTS clone_detection_results (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    dataset text NOT NULL,
    language1 text NOT NULL,
    language2 text NOT NULL,
    representation text NOT NULL,
    positive_count integer,
    negative_count integer,
    total_count integer,
    calibration_count integer,
    test_count integer,
    threshold numeric,
    accuracy numeric,
    precision numeric,
    recall numeric,
    f1 numeric,
    roc_auc numeric,
    average_precision numeric,
    balanced_accuracy numeric,
    mcc numeric,
    details jsonb
);

CREATE TABLE IF NOT EXISTS code_summarization_results (
    id BIGSERIAL PRIMARY KEY,
    created_at timestamptz DEFAULT now(),
    dataset text NOT NULL,
    language text NOT NULL,
    method text NOT NULL,
    representation text NOT NULL,
    train_count integer,
    test_count integer,
    evaluated_count integer,
    k integer,
    bleu numeric,
    meteor numeric,
    rouge1 numeric,
    rouge_l numeric,
    exact_match numeric,
    details jsonb
);

CREATE INDEX IF NOT EXISTS raw_measurement_audit_lookup
    ON raw_measurement_audit (dataset, table_name, language, split, row_id);

CREATE INDEX IF NOT EXISTS baseline_comparison_lookup
    ON baseline_comparison_results (dataset, baseline_name, language1, language2);

CREATE INDEX IF NOT EXISTS dataset_artifact_hashes_lookup
    ON dataset_artifact_hashes (artifact_type, artifact_name);

CREATE INDEX IF NOT EXISTS intrinsic_sensitivity_lookup
    ON intrinsic_sensitivity_results (dataset, task, metric, corruption_type, corruption_level);

CREATE INDEX IF NOT EXISTS stagewise_ablation_lookup
    ON stagewise_ablation_results (dataset, ablation_variant);

CREATE INDEX IF NOT EXISTS downstream_correlation_lookup
    ON downstream_correlation_results (dataset, intrinsic_metric, downstream_metric);

CREATE INDEX IF NOT EXISTS clone_detection_lookup
    ON clone_detection_results (dataset, representation, language1, language2);

CREATE INDEX IF NOT EXISTS code_summarization_lookup
    ON code_summarization_results (dataset, language, method, representation);

DROP VIEW IF EXISTS "v_code_summarization_summary";
CREATE VIEW "public"."v_code_summarization_summary" AS
SELECT
    dataset,
    method,
    representation,
    count(*) AS language_count,
    sum(train_count) AS train_count,
    sum(test_count) AS test_count,
    sum(evaluated_count) AS evaluated_count,
    avg(bleu) AS bleu_mean,
    avg(meteor) AS meteor_mean,
    avg(rouge1) AS rouge1_mean,
    avg(rouge_l) AS rouge_l_mean,
    avg(exact_match) AS exact_match_mean
FROM code_summarization_results
GROUP BY dataset, method, representation
ORDER BY dataset, method, representation;

DROP VIEW IF EXISTS "v_clone_detection_summary";
CREATE VIEW "public"."v_clone_detection_summary" AS
SELECT
    dataset,
    representation,
    count(*) AS pair_count,
    sum(positive_count) AS positive_count,
    sum(negative_count) AS negative_count,
    sum(total_count) AS total_count,
    avg(calibration_count) AS calibration_count_mean,
    avg(test_count) AS test_count_mean,
    avg(threshold) AS threshold_mean,
    avg(accuracy) AS accuracy_mean,
    avg("precision") AS precision_mean,
    avg(recall) AS recall_mean,
    avg(f1) AS f1_mean,
    avg(roc_auc) AS roc_auc_mean,
    avg(average_precision) AS average_precision_mean,
    avg(balanced_accuracy) AS balanced_accuracy_mean,
    avg(mcc) AS mcc_mean
FROM clone_detection_results
GROUP BY dataset, representation
ORDER BY dataset, representation;

DROP VIEW IF EXISTS "v_intrinsic_sensitivity_summary";
CREATE VIEW "public"."v_intrinsic_sensitivity_summary" AS
SELECT
    dataset,
    task,
    metric,
    representation,
    corruption_type,
    corruption_level,
    count(*) AS sample_count,
    avg(baseline_value) AS baseline_mean,
    avg(value) AS value_mean,
    avg(delta) AS delta_mean,
    stddev_samp(value) AS value_std_dev,
    min(value) AS value_min,
    max(value) AS value_max
FROM intrinsic_sensitivity_results
GROUP BY dataset, task, metric, representation, corruption_type, corruption_level
ORDER BY dataset, task, metric, representation, corruption_type, corruption_level;

-- ============================================================
-- GIN indexes for JSONB columns (merged from 4_add_indexes.py)
-- ============================================================

-- c2c tables
CREATE INDEX IF NOT EXISTS idx_c2c_cs_var_original_gin ON public.c2c_cs USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2c_cs_func_original_gin ON public.c2c_cs USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2c_cs_var_unified_gin ON public.c2c_cs USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2c_cs_func_unified_gin ON public.c2c_cs USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2c_cs_pec_data_gin ON public.c2c_cs USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2c_java_var_original_gin ON public.c2c_java USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2c_java_func_original_gin ON public.c2c_java USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2c_java_var_unified_gin ON public.c2c_java USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2c_java_func_unified_gin ON public.c2c_java USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2c_java_pec_data_gin ON public.c2c_java USING gin (pec_data);

-- c2t tables
CREATE INDEX IF NOT EXISTS idx_c2t_cpp_var_original_gin ON public.c2t_cpp USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_cpp_func_original_gin ON public.c2t_cpp USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_cpp_var_unified_gin ON public.c2t_cpp USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_cpp_func_unified_gin ON public.c2t_cpp USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_cpp_pec_data_gin ON public.c2t_cpp USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2t_cs_var_original_gin ON public.c2t_cs USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_cs_func_original_gin ON public.c2t_cs USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_cs_var_unified_gin ON public.c2t_cs USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_cs_func_unified_gin ON public.c2t_cs USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_cs_pec_data_gin ON public.c2t_cs USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2t_go_var_original_gin ON public.c2t_go USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_go_func_original_gin ON public.c2t_go USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_go_var_unified_gin ON public.c2t_go USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_go_func_unified_gin ON public.c2t_go USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_go_pec_data_gin ON public.c2t_go USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2t_java_var_original_gin ON public.c2t_java USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_java_func_original_gin ON public.c2t_java USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_java_var_unified_gin ON public.c2t_java USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_java_func_unified_gin ON public.c2t_java USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_java_pec_data_gin ON public.c2t_java USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2t_javascript_var_original_gin ON public.c2t_javascript USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_javascript_func_original_gin ON public.c2t_javascript USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_javascript_var_unified_gin ON public.c2t_javascript USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_javascript_func_unified_gin ON public.c2t_javascript USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_javascript_pec_data_gin ON public.c2t_javascript USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2t_php_var_original_gin ON public.c2t_php USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_php_func_original_gin ON public.c2t_php USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_php_var_unified_gin ON public.c2t_php USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_php_func_unified_gin ON public.c2t_php USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_php_pec_data_gin ON public.c2t_php USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2t_python_var_original_gin ON public.c2t_python USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_python_func_original_gin ON public.c2t_python USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_python_var_unified_gin ON public.c2t_python USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_python_func_unified_gin ON public.c2t_python USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_python_pec_data_gin ON public.c2t_python USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2t_ruby_var_original_gin ON public.c2t_ruby USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_ruby_func_original_gin ON public.c2t_ruby USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_ruby_var_unified_gin ON public.c2t_ruby USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_ruby_func_unified_gin ON public.c2t_ruby USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_ruby_pec_data_gin ON public.c2t_ruby USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_c2t_rust_var_original_gin ON public.c2t_rust USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_c2t_rust_func_original_gin ON public.c2t_rust USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_c2t_rust_var_unified_gin ON public.c2t_rust USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_rust_func_unified_gin ON public.c2t_rust USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_c2t_rust_pec_data_gin ON public.c2t_rust USING gin (pec_data);

-- heval tables
CREATE INDEX IF NOT EXISTS idx_heval_var_original_gin ON public.heval USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_heval_func_original_gin ON public.heval USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_heval_var_unified_gin ON public.heval USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_heval_func_unified_gin ON public.heval USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_heval_pec_data_gin ON public.heval USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_heval_cpp_var_original_gin ON public.heval_cpp USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_heval_cpp_func_original_gin ON public.heval_cpp USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_heval_cpp_var_unified_gin ON public.heval_cpp USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_heval_cpp_func_unified_gin ON public.heval_cpp USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_heval_cpp_pec_data_gin ON public.heval_cpp USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_heval_go_var_original_gin ON public.heval_go USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_heval_go_func_original_gin ON public.heval_go USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_heval_go_var_unified_gin ON public.heval_go USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_heval_go_func_unified_gin ON public.heval_go USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_heval_go_pec_data_gin ON public.heval_go USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_heval_java_var_original_gin ON public.heval_java USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_heval_java_func_original_gin ON public.heval_java USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_heval_java_var_unified_gin ON public.heval_java USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_heval_java_func_unified_gin ON public.heval_java USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_heval_java_pec_data_gin ON public.heval_java USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_heval_javascript_var_original_gin ON public.heval_javascript USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_heval_javascript_func_original_gin ON public.heval_javascript USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_heval_javascript_var_unified_gin ON public.heval_javascript USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_heval_javascript_func_unified_gin ON public.heval_javascript USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_heval_javascript_pec_data_gin ON public.heval_javascript USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_heval_python_var_original_gin ON public.heval_python USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_heval_python_func_original_gin ON public.heval_python USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_heval_python_var_unified_gin ON public.heval_python USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_heval_python_func_unified_gin ON public.heval_python USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_heval_python_pec_data_gin ON public.heval_python USING gin (pec_data);

CREATE INDEX IF NOT EXISTS idx_heval_rust_var_original_gin ON public.heval_rust USING gin (var_original);
CREATE INDEX IF NOT EXISTS idx_heval_rust_func_original_gin ON public.heval_rust USING gin (func_original);
CREATE INDEX IF NOT EXISTS idx_heval_rust_var_unified_gin ON public.heval_rust USING gin (var_unified);
CREATE INDEX IF NOT EXISTS idx_heval_rust_func_unified_gin ON public.heval_rust USING gin (func_unified);
CREATE INDEX IF NOT EXISTS idx_heval_rust_pec_data_gin ON public.heval_rust USING gin (pec_data);
