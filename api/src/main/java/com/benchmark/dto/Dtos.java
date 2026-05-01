package com.benchmark.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

// ── Resposta: User ─────────────────────────────────────────────────────────────
@Data @AllArgsConstructor @NoArgsConstructor
class UserDTO {
    private Long id;
    private String name;
    private String email;
    private LocalDateTime createdAt;
}

// ── Resposta: item dentro de um pedido ────────────────────────────────────────
@Data @AllArgsConstructor @NoArgsConstructor
class OrderItemDTO {
    private Long itemId;
    private Long productId;
    private String productName;
    private String categoryName;
    private Integer quantity;
    private BigDecimal unitPrice;
}

// ── Resposta: detalhe completo de um pedido (leitura complexa) ────────────────
@Data @AllArgsConstructor @NoArgsConstructor
public class OrderDetailDTO {
    private Long orderId;
    private String status;
    private BigDecimal total;
    private LocalDateTime createdAt;
    private Long userId;
    private String userName;
    private List<OrderItemDTO> items;
}

// ── Request: criação de pedido ─────────────────────────────────────────────────
@Data @AllArgsConstructor @NoArgsConstructor
public class OrderRequestDTO {
    private Long userId;
    private List<ItemRequestDTO> items;

    @Data @AllArgsConstructor @NoArgsConstructor
    public static class ItemRequestDTO {
        private Long productId;
        private Integer quantity;
        private BigDecimal unitPrice;
    }
}
