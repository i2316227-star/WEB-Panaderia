-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 04-11-2026 a las 17:42:46
-- Versión del servidor: 10.11.16-MariaDB
-- Versión de PHP: 8.5.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `dvida_db`
--
CREATE DATABASE IF NOT EXISTS `dvida_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `dvida_db`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pedidos`
--

DROP TABLE IF EXISTS `pedidos`;
CREATE TABLE `pedidos` (
  `id` int(11) NOT NULL,
  `cliente` varchar(100) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `total` decimal(10,2) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `fecha` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pedidos`
--

INSERT INTO `pedidos` (`id`, `cliente`, `usuario_id`, `total`, `estado`, `fecha`) VALUES
(1, 'Brayan Flores', 2, 17.00, 'Pagado', '2026-10-15 16:40:03'),
(2, 'David Carlos', 3, 6.00, 'Pendiente', '2026-10-15 16:31:28'),
(3, 'David Carlos', 3, 3.00, 'Cancelado', '2026-10-15 16:31:38'),
(4, 'Carlos', NULL, 4.00, 'Pagado', '2026-10-15 16:43:24'),
(5, 'Brayan Flores', 2, 1.00, 'Pendiente', '2026-11-04 11:35:57');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pedido_items`
--

DROP TABLE IF EXISTS `pedido_items`;
CREATE TABLE `pedido_items` (
  `id` int(11) NOT NULL,
  `pedido_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio_unitario` decimal(8,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pedido_items`
--

INSERT INTO `pedido_items` (`id`, `pedido_id`, `producto_id`, `cantidad`, `precio_unitario`, `subtotal`) VALUES
(1, 1, 3, 5, 1.00, 5.00),
(2, 1, 2, 9, 1.00, 9.00),
(3, 1, 4, 3, 1.00, 3.00),
(4, 2, 7, 2, 2.00, 4.00),
(5, 2, 5, 1, 2.00, 2.00),
(6, 3, 3, 3, 1.00, 3.00),
(7, 4, 7, 2, 2.00, 4.00),
(8, 5, 3, 1, 1.00, 1.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos`
--

DROP TABLE IF EXISTS `productos`;
CREATE TABLE `productos` (
  `id` int(11) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `categoria` varchar(50) DEFAULT NULL,
  `precio` decimal(8,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `productos`
--

INSERT INTO `productos` (`id`, `nombre`, `categoria`, `precio`) VALUES
(1, 'Pan francés (5 unidades)', 'Panes', 1.00),
(2, 'Pan Chapla (5 unidades)', 'Panes', 1.00),
(3, 'Pan de Camote (5 unidades)', 'Panes', 1.00),
(4, 'Pan de Mantequilla (5 unidades)', 'Panes', 1.00),
(5, 'Mil Hojas', 'Pastelería', 2.00),
(6, 'Alfajores', 'Pastelería', 1.00),
(7, 'Leche Asada', 'Pastelería', 2.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `rol` varchar(20) NOT NULL DEFAULT 'cliente'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `nombre`, `email`, `password`, `rol`) VALUES
(1, 'Denis Carlos', 'i2316227@continental.edu.pe', 'scrypt:32768:8:1$ZXLapbg70pPrZ4u1$e84beb6f3cc50e0e0473f878c8b417c1fb72c6c1d4077020e77aa9fecfee160b83a23a9be0168f37dd32ac4da4e4d69dc25b823dd445d995f6f37da03d957821', 'admin'),
(2, 'Brayan Flores', 'i2522049@continental.edu.pe', 'scrypt:32768:8:1$o5BCqW22Vnco1dR1$5f90e38cf716664ce46e49fd88d6d2d0aa2179a34c46158a257e69d2eac71265425529dc30efdce035e6c5ea6caafb42f0ebcc35cc5ec32997a0846b01c9d309', 'cliente'),
(3, 'David Carlos', 'david12@gmail.com', 'scrypt:32768:8:1$bOgxo1LM0QYf7EYb$425d1b0b620508ac8f5904b51bdd661354d803f132a43045ddaa74da606085b68dce5a3c5a302e5b06db209fb276c5e8132bb0ef63fef5168c08d69de4dfc495', 'cliente');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `pedidos`
--
ALTER TABLE `pedidos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_pedidos_usuario` (`usuario_id`);

--
-- Indices de la tabla `pedido_items`
--
ALTER TABLE `pedido_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_items_pedido` (`pedido_id`),
  ADD KEY `fk_items_producto` (`producto_id`);

--
-- Indices de la tabla `productos`
--
ALTER TABLE `productos`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `pedidos`
--
ALTER TABLE `pedidos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `pedido_items`
--
ALTER TABLE `pedido_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `productos`
--
ALTER TABLE `productos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `pedidos`
--
ALTER TABLE `pedidos`
  ADD CONSTRAINT `fk_pedidos_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL;

--
-- Filtros para la tabla `pedido_items`
--
ALTER TABLE `pedido_items`
  ADD CONSTRAINT `fk_items_pedido` FOREIGN KEY (`pedido_id`) REFERENCES `pedidos` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_items_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
