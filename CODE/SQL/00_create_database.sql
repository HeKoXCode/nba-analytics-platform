/* Idempotent database bootstrap. The loader replaces $(NBA_DATABASE) safely. */
IF DB_ID(N'$(NBA_DATABASE)') IS NULL
BEGIN
    EXEC(N'CREATE DATABASE [' + '$(NBA_DATABASE)' + N']');
END;
GO
