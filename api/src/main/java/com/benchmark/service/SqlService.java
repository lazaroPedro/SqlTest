package com.benchmark.service;

import com.benchmark.dto.OrderRequestDTO;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SqlService {

    private final JdbcTemplate jdbc;

    // ── 1. Leitura Simples: SELECT user por ID ─────────────────────────────────
    public Map<String, Object> findUserById(Long id) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT id, name, email, created_at FROM users WHERE id = ?", id);

        if (rows.isEmpty()) throw new EntityNotFoundException("User not found: " + id);
        return rows.get(0);
    }

    // ── 2. Escrita: INSERT de pedido com itens (transação explícita) ───────────
    @Transactional
    public Long createOrder(OrderRequestDTO req) {
        BigDecimal total = req.getItems().stream()
                .map(i -> i.getUnitPrice().multiply(BigDecimal.valueOf(i.getQuantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        // INSERT order
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbc.update(conn -> {
            PreparedStatement ps = conn.prepareStatement(
                    "INSERT INTO orders (user_id, total, status, created_at) VALUES (?, ?, 'pending', ?)",
                    Statement.RETURN_GENERATED_KEYS);
            ps.setLong(1, req.getUserId());
            ps.setBigDecimal(2, total);
            ps.setTimestamp(3, Timestamp.valueOf(LocalDateTime.now()));
            return ps;
        }, keyHolder);

        Long orderId = keyHolder.getKey().longValue();

        // INSERT order_items (batch)
        jdbc.batchUpdate(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                req.getItems(), req.getItems().size(),
                (ps, item) -> {
                    ps.setLong(1, orderId);
                    ps.setLong(2, item.getProductId());
                    ps.setInt(3, item.getQuantity());
                    ps.setBigDecimal(4, item.getUnitPrice());
                });

        return orderId;
    }

    // ── 3. Leitura Complexa: JOIN completo em SQL nativo (1 única query) ───────
    public List<Map<String, Object>> findOrderWithDetails(Long id) {
        String sql = """
                SELECT
                    o.id          AS order_id,
                    o.status,
                    o.total,
                    o.created_at,
                    u.id          AS user_id,
                    u.name        AS user_name,
                    oi.id         AS item_id,
                    oi.quantity,
                    oi.unit_price,
                    p.id          AS product_id,
                    p.name        AS product_name,
                    c.name        AS category_name
                FROM orders o
                    JOIN users       u  ON u.id  = o.user_id
                    JOIN order_items oi ON oi.order_id  = o.id
                    JOIN products    p  ON p.id  = oi.product_id
                    JOIN categories  c  ON c.id  = p.category_id
                WHERE o.id = ?
                ORDER BY oi.id
                """;

        List<Map<String, Object>> rows = jdbc.queryForList(sql, id);
        if (rows.isEmpty()) throw new EntityNotFoundException("Order not found: " + id);
        return rows;
    }
}
