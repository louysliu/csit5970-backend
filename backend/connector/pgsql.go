package connector

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// PgConfig holds the configuration for PostgreSQL connection
type PgConfig struct {
	Host         string
	Port         int
	User         string
	Password     string
	DatabaseName string
}

var (
	pgPool *pgxpool.Pool
)

func InitPGPool(ctx context.Context, config *PgConfig) error {
	url := fmt.Sprintf("postgres://%s:%s@%s:%d/%s", config.User, config.Password, config.Host, config.Port, config.DatabaseName)
	var err error
	pgPool, err = pgxpool.New(ctx, url)
	return err
}

func ClosePGPool() {
	pgPool.Close()
}

// return a list of results for a given job id, sorted by frame index
func QueryJobResults(ctx context.Context, jobID string) ([]string, error) {
	rows, err := pgPool.Query(ctx, "SELECT result FROM yolo WHERE job_id = $1 ORDER BY frame_id", jobID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return pgx.CollectRows(rows, pgx.RowTo[string])
}
