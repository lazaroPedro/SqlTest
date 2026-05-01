package com.benchmark.controller;

import com.benchmark.dto.OrderRequestDTO;
import com.benchmark.service.SqlService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/sql")
@RequiredArgsConstructor
public class SqlController {

    private final SqlService sqlService;

    /**
     * LEITURA SIMPLES — SELECT user por ID via SQL nativo (JdbcTemplate)
     * GET /api/sql/users/{id}
     */
    @GetMapping("/users/{id}")
    public ResponseEntity<Map<String, Object>> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(sqlService.findUserById(id));
    }

    /**
     * ESCRITA — INSERT de pedido + itens via SQL nativo (batch)
     * POST /api/sql/orders
     */
    @PostMapping("/orders")
    public ResponseEntity<Map<String, Long>> createOrder(@RequestBody OrderRequestDTO req) {
        Long orderId = sqlService.createOrder(req);
        return ResponseEntity.ok(Map.of("orderId", orderId));
    }

    /**
     * LEITURA COMPLEXA — JOIN completo em SQL nativo (1 query, sem N+1)
     * GET /api/sql/orders/{id}/details
     */
    @GetMapping("/orders/{id}/details")
    public ResponseEntity<List<Map<String, Object>>> getOrderDetails(@PathVariable Long id) {
        return ResponseEntity.ok(sqlService.findOrderWithDetails(id));
    }
}
