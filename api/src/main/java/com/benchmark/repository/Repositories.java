package com.benchmark.repository;

import com.benchmark.entity.Order;
import com.benchmark.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    // Leitura simples — SELECT por ID (gerado automaticamente)
}

@Repository
interface OrderRepository extends JpaRepository<Order, Long> {

    // ── ORM com problema N+1: carrega o pedido; itens são buscados em queries separadas
    Optional<Order> findById(Long id);

    // ── ORM otimizado: JOIN FETCH traz tudo em uma única query
    @Query("""
        SELECT DISTINCT o FROM Order o
        JOIN FETCH o.user u
        JOIN FETCH o.items i
        JOIN FETCH i.product p
        JOIN FETCH p.category
        WHERE o.id = :id
    """)
    Optional<Order> findByIdWithDetails(@Param("id") Long id);
}
