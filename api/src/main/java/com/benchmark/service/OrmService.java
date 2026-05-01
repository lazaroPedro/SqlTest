package com.benchmark.service;

import com.benchmark.dto.OrderDetailDTO;
import com.benchmark.dto.OrderRequestDTO;
import com.benchmark.entity.*;
import com.benchmark.repository.OrderRepository;
import com.benchmark.repository.UserRepository;
import jakarta.persistence.EntityNotFoundException;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class OrmService {

    private final UserRepository userRepo;
    private final OrderRepository orderRepo;

    // ── 1. Leitura Simples: SELECT user por ID ─────────────────────────────────
    public User findUserById(Long id) {
        return userRepo.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("User not found: " + id));
    }

    // ── 2. Escrita: INSERT de pedido com itens ─────────────────────────────────
    @Transactional
    public Order createOrder(OrderRequestDTO req) {
        User user = userRepo.findById(req.getUserId())
                .orElseThrow(() -> new EntityNotFoundException("User not found"));

        Order order = new Order();
        order.setUser(user);
        order.setStatus("pending");
        order.setCreatedAt(LocalDateTime.now());

        List<OrderItem> items = req.getItems().stream().map(i -> {
            Product prod = new Product();
            prod.setId(i.getProductId());   // referência sem carregar

            OrderItem item = new OrderItem();
            item.setOrder(order);
            item.setProduct(prod);
            item.setQuantity(i.getQuantity());
            item.setUnitPrice(i.getUnitPrice());
            return item;
        }).toList();

        order.setItems(items);
        order.setTotal(items.stream()
                .map(i -> i.getUnitPrice().multiply(BigDecimal.valueOf(i.getQuantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add));

        return orderRepo.save(order);   // cascade salva os itens
    }

    // ── 3a. Leitura Complexa com N+1 (ORM padrão / sem otimização) ────────────
    //   O Hibernate dispara 1 query para o pedido + N queries para cada item
    public Order findOrderWithN1(Long id) {
        Order order = orderRepo.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Order not found: " + id));
        // Forçar carregamento dos itens (N+1 acontece aqui dentro da transação aberta)
        order.getItems().size();
        order.getItems().forEach(i -> {
            i.getProduct().getName();       // +1 por produto
            i.getProduct().getCategory().getName(); // +1 por categoria
        });
        return order;
    }

    // ── 3b. Leitura Complexa Otimizada (JOIN FETCH — 1 única query) ───────────
    public Order findOrderOptimized(Long id) {
        return orderRepo.findByIdWithDetails(id)
                .orElseThrow(() -> new EntityNotFoundException("Order not found: " + id));
    }
}
