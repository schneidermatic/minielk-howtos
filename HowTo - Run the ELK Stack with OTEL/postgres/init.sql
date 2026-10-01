CREATE TABLE products (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL
);

CREATE TABLE orders (
    id         SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    value      NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 50 sample products: laptops, phones, monitors, keyboards and mice
INSERT INTO products (name, price)
SELECT (ARRAY['Laptop','Phone','Monitor','Keyboard','Mouse'])[1 + (g % 5)] || ' Model ' || g,
       round((10 + random() * 990)::numeric, 2)
FROM generate_series(1, 50) AS g;
