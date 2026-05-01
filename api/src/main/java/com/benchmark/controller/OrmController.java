package com.benchmark.controller;

import com.benchmark.dto.OrderRequestDTO;
import com.benchmark.entity.Order;
import com.benchmark.entity.User;
import com.benchmark.service.OrmService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/orm")
@RequiredArgsConstructor
public class OrmController {

    private final OrmService ormService;

    /**
     * LEITURA SIMPLES — SELECT user por ID via ORM (Hibernate gera o SQL)
     * GET /api/orm/users/{id}
     */
    @GetMapping("/users/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(ormService.findUserById(id));
    }

    /**
     * ESCRITA — INSERT de pedido + itens via ORM (cascade)
     * POST /api/orm/orders
     */
    @PostMapping("/orders")
    public ResponseEntity<Order> createOrder(@RequestBody OrderRequestDTO req) {
        return ResponseEntity.ok(ormService.createOrder(req));
    }

    /**
     * LEITURA COMPLEXA com N+1 — ORM sem otimização
     * O Hibernate dispara múltiplas queries (1 para o pedido + N para itens/produtos/categorias)
     * GET /api/orm/orders/{id}/details
     */
    @GetMapping("/orders/{id}/details")
    public ResponseEntity<Order> getOrderN1(@PathVariable Long id) {
        return ResponseEntity.ok(ormService.findOrderWithN1(id));
    }

    /**
     * LEITURA COMPLEXA OTIMIZADA — ORM com JOIN FETCH
     * Uma única query traz pedido + itens + produtos + categorias
     * GET /api/orm/orders/{id}/details/optimized
     */
    @GetMapping("/orders/{id}/details/optimized")
    public ResponseEntity<Order> getOrderOptimized(@PathVariable Long id) {
        return ResponseEntity.ok(ormService.findOrderOptimized(id));
    }
}
