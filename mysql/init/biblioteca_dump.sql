-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: biblioteca
-- ------------------------------------------------------
-- Server version	8.0.42-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `biblioteca`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `biblioteca` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `biblioteca`;

--
-- Table structure for table `acessos`
--

DROP TABLE IF EXISTS `acessos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `acessos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  `ip` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sucesso` tinyint(1) NOT NULL,
  `user_agent` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `acessos_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `acessos`
--

LOCK TABLES `acessos` WRITE;
/*!40000 ALTER TABLE `acessos` DISABLE KEYS */;
INSERT INTO `acessos` VALUES (1,2,'2025-05-10 01:58:14','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(2,1,'2025-05-10 01:58:31','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(3,1,'2025-05-10 01:58:35','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(4,1,'2025-05-10 02:00:03','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(5,1,'2025-05-12 00:37:59','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(6,1,'2025-05-12 00:51:08','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(7,2,'2025-05-12 00:51:25','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(8,2,'2025-05-12 00:51:27','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(9,2,'2025-05-12 00:52:05','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(10,1,'2025-05-12 00:57:00','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(11,1,'2025-05-12 00:57:02','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(12,2,'2025-05-12 00:57:04','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(13,2,'2025-05-12 00:57:06','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(14,1,'2025-05-12 00:57:18','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(15,1,'2025-05-12 01:02:45','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(16,1,'2025-05-12 01:02:51','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(17,1,'2025-05-12 01:04:16','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(18,1,'2025-05-12 01:05:05','10.0.11.198',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(19,1,'2025-05-12 12:29:07','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(20,1,'2025-05-12 14:55:34','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(21,1,'2025-05-12 17:38:18','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(22,2,'2025-05-12 17:38:22','10.0.10.147',0,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(23,1,'2025-05-12 17:38:36','10.0.10.147',0,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(24,2,'2025-05-12 17:38:39','10.0.10.147',0,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(25,1,'2025-05-12 17:40:33','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(26,1,'2025-05-12 17:40:44','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(27,1,'2025-05-12 17:40:46','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(28,1,'2025-05-12 17:43:27','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(29,NULL,'2025-05-12 17:43:29','10.0.10.147',0,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(30,NULL,'2025-05-12 17:43:32','10.0.10.147',0,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(31,1,'2025-05-12 17:43:35','10.0.10.147',0,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(32,1,'2025-05-12 17:45:29','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(33,1,'2025-05-12 17:49:11','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(34,1,'2025-05-12 17:59:39','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(35,1,'2025-05-12 17:59:41','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(36,1,'2025-05-12 18:00:16','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(37,1,'2025-05-12 18:00:17','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(38,NULL,'2025-05-12 18:00:21','10.0.10.147',0,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(39,1,'2025-05-12 18:00:27','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(40,1,'2025-05-12 18:02:29','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(41,2,'2025-05-12 18:04:25','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(42,2,'2025-05-12 18:04:27','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(45,1,'2025-05-12 18:04:41','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(46,1,'2025-05-12 18:09:26','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(48,1,'2025-05-12 18:09:37','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(49,1,'2025-05-12 18:14:44','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(50,2,'2025-05-12 18:14:47','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(51,2,'2025-05-12 18:21:42','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(52,1,'2025-05-12 18:21:49','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(53,2,'2025-05-12 18:25:00','200.19.220.175',1,'Mozilla/5.0 (iPhone; CPU iPhone OS 18_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Mobile/15E148 Safari/604.1'),(54,1,'2025-05-12 18:25:36','10.0.111.2',1,'Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/136.0.7103.91 Mobile/15E148 Safari/604.1'),(55,1,'2025-05-12 18:27:18','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(56,1,'2025-05-12 18:28:26','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(57,1,'2025-05-12 18:29:02','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(58,1,'2025-05-12 18:29:17','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(59,1,'2025-05-12 18:30:09','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(60,NULL,'2025-05-12 18:30:13','10.0.10.147',0,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(61,1,'2025-05-12 18:30:16','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(62,1,'2025-05-12 18:40:05','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(63,1,'2025-05-12 18:40:17','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(64,1,'2025-05-12 18:42:21','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(65,1,'2025-05-12 18:47:10','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'),(66,1,'2025-05-12 18:48:44','10.0.10.147',1,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36');
/*!40000 ALTER TABLE `acessos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `aluno`
--

DROP TABLE IF EXISTS `aluno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `aluno` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `turma` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `barcode_img` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_aluno_codigo` (`codigo`),
  KEY `ix_aluno_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `aluno`
--

LOCK TABLES `aluno` WRITE;
/*!40000 ALTER TABLE `aluno` DISABLE KEYS */;
INSERT INTO `aluno` VALUES (1,'001','Carlos Eduardo de Macedo Costa','101','001.png'),(2,'002','Júlia Grasiela Bucci de Macedo Costa','102','002.png'),(3,'003','Filomena Felina de Macedo Costa Miau','103','003.png'),(4,'004','Phoebe Felina de Macedo Costa Miau','104','004.png'),(5,'010','Carlos Miguel Augusto da Silva','110','010.png'),(6,'011','Juliana da Silva Saulo','111','011.png');
/*!40000 ALTER TABLE `aluno` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `emprestimo`
--

DROP TABLE IF EXISTS `emprestimo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `emprestimo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `aluno_id` int NOT NULL,
  `livro_id` int NOT NULL,
  `data_emprestimo` date NOT NULL,
  `data_prevista_devolucao` date NOT NULL,
  `data_devolucao` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `aluno_id` (`aluno_id`),
  KEY `livro_id` (`livro_id`),
  KEY `ix_emprestimo_id` (`id`),
  CONSTRAINT `emprestimo_ibfk_1` FOREIGN KEY (`aluno_id`) REFERENCES `aluno` (`id`),
  CONSTRAINT `emprestimo_ibfk_2` FOREIGN KEY (`livro_id`) REFERENCES `livro` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `emprestimo`
--

LOCK TABLES `emprestimo` WRITE;
/*!40000 ALTER TABLE `emprestimo` DISABLE KEYS */;
INSERT INTO `emprestimo` VALUES (1,1,1,'2025-05-12','2025-05-19','2025-05-12'),(2,1,1,'2025-05-12','2025-05-19','2025-05-12'),(3,2,3,'2025-05-12','2025-05-19','2025-05-12'),(4,4,1,'2025-05-12','2025-05-19','2025-05-12'),(5,3,1,'2025-05-12','2025-05-19','2025-05-12'),(6,1,1,'2025-05-12','2025-05-19','2025-05-12'),(7,1,1,'2025-05-12','2025-05-19','2025-05-12'),(8,2,2,'2025-05-12','2025-05-19','2025-05-12'),(9,1,2,'2025-05-12','2025-05-19','2025-05-12'),(10,1,3,'2025-05-12','2025-05-19','2025-05-12'),(11,1,4,'2025-05-12','2025-05-19','2025-05-12'),(12,1,1,'2025-05-12','2025-05-19','2025-05-12'),(13,1,4,'2025-05-12','2025-05-19','2025-05-12'),(14,1,3,'2025-05-12','2025-05-19','2025-05-12'),(15,2,2,'2025-05-12','2025-05-19','2025-05-12'),(16,1,1,'2025-05-12','2025-05-19','2025-05-12'),(17,2,3,'2025-05-12','2025-05-19','2025-05-12'),(18,1,1,'2025-05-12','2025-05-19','2025-05-12'),(19,1,1,'2025-05-12','2025-05-19','2025-05-12'),(20,1,1,'2025-05-12','2025-05-19','2025-05-12'),(21,1,3,'2025-05-12','2025-05-19','2025-05-12'),(22,2,2,'2025-05-12','2025-05-19','2025-05-12'),(23,3,4,'2025-05-12','2025-05-19','2025-05-12'),(24,1,1,'2025-05-12','2025-06-07','2025-05-12'),(25,1,2,'2025-05-12','2025-05-23','2025-05-12'),(26,1,1,'2025-05-12','2025-05-22','2025-05-12'),(27,1,1,'2025-05-12','2025-06-26','2025-05-12'),(28,1,3,'2025-05-12','2025-05-15','2025-05-12'),(29,2,4,'2025-05-12','2025-05-20','2025-05-12');
/*!40000 ALTER TABLE `emprestimo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `livro`
--

DROP TABLE IF EXISTS `livro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `livro` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `titulo` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `autor` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ano_publicacao` int DEFAULT NULL,
  `categoria` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `situacao` enum('disponível','emprestado') COLLATE utf8mb4_unicode_ci NOT NULL,
  `barcode_img` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_livro_codigo` (`codigo`),
  KEY `ix_livro_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `livro`
--

LOCK TABLES `livro` WRITE;
/*!40000 ALTER TABLE `livro` DISABLE KEYS */;
INSERT INTO `livro` VALUES (1,'001','Viagem ao Centro da Terra','Juliu Verni',1890,'Ficção Científica','disponível','001.png'),(2,'002','A volta dos que não foram','Didi Mocó',2026,'Comédia','disponível','002.png'),(3,'003','Pai Rico Pai Pobre','Robert Kiozaki',1999,'Finanças','disponível','003.png'),(4,'004','O milagre da manhã','Dan Conan',1980,'Saúde','disponível','004.png'),(5,'005','MemóriasdeumaCidadeEsquecida','LarissaCosta',2024,'Aventura','disponível','005.png'),(6,'006','CódigosdaMente','GustavoAlmeida',2023,'ThrillerPsicológico','disponível','006.png'),(7,'007','OÚltimoVerso','BeatrizRocha',2019,'Poesia','disponível','007.png'),(8,'008','LabirintodeMentiras','TiagoMartins',2022,'Suspense','disponível','008.png');
/*!40000 ALTER TABLE `livro` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `criado_em` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'macedo','scrypt:32768:8:1$mqi90oB2QNr4T6WW$7bf1addb3cfa972b353c64cb81c0db761179ff2d38ecfa2bdbefc35ed8da6012d56f5d7f67d5d74219f51e9348a718f28c601d06a5772074b727f0618b733ac6','2025-05-10 01:57:30'),(2,'ju','scrypt:32768:8:1$JUVeDm85pRTHYu3w$03b649ca22294abe1de44d5758dea80d5458d10d6a5195b2fdbb7a7ee52a6401114acc063fa6b956288b90f30c4ec5cc5b982294e23d44e37b7734ab78343c66','2025-05-10 01:57:43');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-05-13 20:19:26
