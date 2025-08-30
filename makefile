.PHONY: dev prod up down logs test

dev:
\tdocker compose -f compose.dev.yml up

prod:
\tdocker compose -f compose.prod.yml up --build -d

down:
\tdocker compose -f compose.dev.yml down || true
\tdocker compose -f compose.prod.yml down || true

logs:
\tdocker compose -f compose.prod.yml logs -f

test:
\tpytest -q -rxXs
