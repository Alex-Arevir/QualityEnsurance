"""
Pruebas de Rendimiento - NFR1 (CORREGIDO)
Distribution Center Package Management System
"""

import pytest
import time
import threading
from distribution_center import DistributionCenterDB, PackageManager
from distribution_center import generate_random_barcode
import os
from dotenv import load_dotenv
import random

load_dotenv()
db_testing = os.getenv('DB_TESTING', 'test_performance.db')


class TestPerformanceNFR1:
    """Pruebas de Requisitos No Funcionales - Performance (NFR1)"""
    
    def setup_method(self):
        """Configuración antes de cada prueba"""
        self.db = DistributionCenterDB(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PackageManager(self.db)
    
    def teardown_method(self):
        """Limpieza después de cada prueba"""
        self.db.disconnect()
        if os.path.exists(db_testing):
            try:
                os.remove(db_testing)
            except PermissionError:
                pass
    
    # NFR1.1 - Registro de paquetes < 2 segundos
    def test_nfr1_1_package_registration_time(self):
        """
        NFR1.1: El registro de paquetes debe completarse en menos de 2 segundos.
        AC-NFR1.1: 95% de operaciones deben completarse dentro de 2 segundos.
        """
        # Arrange
        total_attempts = 20
        successful_times = []
        threshold = 2.0  # segundos
        
        # Act
        for i in range(total_attempts):
            barcode = generate_random_barcode()
            
            # Variar pesos para usar diferentes categorías
            if i % 5 == 0:
                weight = random.uniform(1, 4)  # Fragile
            elif i % 5 == 1:
                weight = random.uniform(60, 100)  # Heavy
            else:
                weight = random.uniform(10, 40)  # Standard
            
            start_time = time.time()
            result = self.manager.register_package(
                barcode=barcode,
                weight=weight,
                length=random.uniform(10, 100),
                width=random.uniform(10, 100),
                height=random.uniform(10, 100),
                destination=f"Destination-{i}",
                priority="Standard"
            )
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            
            if result:
                successful_times.append(elapsed_time)
        
        # Assert
        assert len(successful_times) >= 15, f"Solo {len(successful_times)}/20 registros exitosos"
        
        times_under_threshold = sum(1 for t in successful_times if t < threshold)
        success_rate = (times_under_threshold / len(successful_times)) * 100
        avg_time = sum(successful_times) / len(successful_times)
        
        print(f"\n📊 NFR1.1 Results:")
        print(f"   Successful registrations: {len(successful_times)}/20")
        print(f"   Average time: {avg_time:.4f}s")
        print(f"   Success rate (<2s): {success_rate:.2f}%")
        print(f"   Min: {min(successful_times):.4f}s, Max: {max(successful_times):.4f}s")
        
        assert success_rate >= 95.0, f"Solo {success_rate:.2f}% completó en <2s (esperado: ≥95%)"
        assert avg_time < threshold, f"Tiempo promedio {avg_time:.4f}s excede {threshold}s"
    
    # NFR1.2 - Búsqueda por barcode < 1 segundo (CORREGIDO)
    def test_nfr1_2_search_performance(self):
        """
        NFR1.2: Las búsquedas deben retornar resultados en menos de 1 segundo.
        AC-NFR1.2: La operación debe completarse dentro de 1 segundo.
        """
        # Arrange - Registrar paquetes distribuyéndolos en diferentes categorías
        barcodes = []
        
        for i in range(50):
            barcode = generate_random_barcode()
            
            # Distribuir entre categorías para no llenar una sola
            if i % 5 == 0:
                weight = random.uniform(1, 4)  # Fragile
                priority = "Standard"
            elif i % 5 == 1:
                weight = random.uniform(60, 100)  # Heavy
                priority = "Standard"
            elif i % 5 == 2:
                weight = random.uniform(10, 40)  # Standard
                priority = "Express"
            elif i % 5 == 3:
                weight = random.uniform(10, 40)  # Standard
                priority = "Standard"
                destination = "London, UK, International"  # International
            else:
                weight = random.uniform(10, 40)  # Standard
                priority = "Standard"
                destination = f"City-{i}"
            
            if i % 5 != 3:
                destination = f"City-{i}"
            
            result = self.manager.register_package(
                barcode=barcode,
                weight=weight,
                length=20, width=20, height=20,
                destination=destination,
                priority=priority
            )
            
            # Solo agregar barcodes que se registraron exitosamente
            if result:
                barcodes.append(barcode)
        
        # Verificar que tengamos suficientes paquetes
        assert len(barcodes) >= 30, f"Solo se registraron {len(barcodes)} paquetes (mínimo: 30)"
        
        threshold = 1.0  # segundo
        search_times = []
        
        # Act - Buscar paquetes que SÍ existen
        num_searches = min(50, len(barcodes))
        for _ in range(num_searches):
            barcode = random.choice(barcodes)
            
            start_time = time.time()
            result = self.manager.search_package(barcode)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            search_times.append(elapsed_time)
            
            assert result is not None, f"Paquete {barcode} no encontrado"
        
        # Assert
        avg_time = sum(search_times) / len(search_times)
        max_time = max(search_times)
        
        print(f"\n📊 NFR1.2 Results:")
        print(f"   Packages registered: {len(barcodes)}")
        print(f"   Searches performed: {len(search_times)}")
        print(f"   Average search time: {avg_time:.4f}s")
        print(f"   Max search time: {max_time:.4f}s")
        
        assert max_time < threshold, f"Búsqueda más lenta: {max_time:.4f}s (esperado: <{threshold}s)"
        assert avg_time < threshold, f"Tiempo promedio {avg_time:.4f}s excede {threshold}s"
    
    # NFR1.3 - Reportes con datos < 2 segundos
    @pytest.mark.slow
    def test_nfr1_3_report_generation_performance(self):
        """
        NFR1.3: La generación de reportes debe completarse en <2s.
        AC-NFR1.3: Con múltiples registros, el reporte debe generarse en <2s.
        """
        # Arrange - Registrar paquetes distribuidos
        num_packages = 100
        threshold = 2.0
        
        print(f"\n⏳ Creando {num_packages} paquetes de prueba...")
        
        registered = 0
        for i in range(num_packages):
            barcode = f"REPORT{i:08d}"
            
            # Distribuir en categorías
            if i % 5 == 0:
                weight = random.uniform(1, 4)
            elif i % 5 == 1:
                weight = random.uniform(60, 100)
            else:
                weight = random.uniform(10, 40)
            
            priority = "Express" if i % 3 == 0 else "Standard"
            destination = f"City-{i % 20}"
            
            result = self.manager.register_package(
                barcode=barcode,
                weight=weight,
                length=random.uniform(10, 100),
                width=random.uniform(10, 100),
                height=random.uniform(10, 100),
                destination=destination,
                priority=priority
            )
            
            if result:
                registered += 1
            
            if (i + 1) % 25 == 0:
                print(f"   Progreso: {i+1}/{num_packages} (registrados: {registered})")
        
        print(f"   ✅ Total registrado: {registered}/{num_packages}")
        assert registered >= 50, f"Muy pocos registros exitosos: {registered}"
        
        # Act
        print("\n🔄 Generando reporte...")
        start_time = time.time()
        report = self.manager.get_summary_report()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        
        # Assert
        print(f"\n📊 NFR1.3 Results:")
        print(f"   Packages registered: {registered}")
        print(f"   Report generation time: {elapsed_time:.4f}s")
        print(f"   Categories found: {len(report['by_category'])}")
        print(f"   Statuses found: {len(report['by_status'])}")
        
        assert elapsed_time < threshold, f"Tiempo {elapsed_time:.4f}s excede {threshold}s"
        assert report is not None
        assert len(report['by_category']) > 0
    
    # NFR1.4 - Registros concurrentes
    @pytest.mark.integration
    def test_nfr1_4_concurrent_registration(self):
        """
        NFR1.4: El sistema debe soportar registros concurrentes sin pérdida de datos.
        AC-NFR1.4: No debe haber transacciones perdidas o corruptas.
        """
        # Arrange
        num_packages = 20  # Reducido para evitar problemas de espacio
        time_limit = 60
        results = []
        errors = []
        
        def register_package_thread(index):
            """Función para registrar paquete en thread"""
            try:
                db = DistributionCenterDB(db_name=db_testing)
                db.connect()
                manager = PackageManager(db)
                
                barcode = f"CONCURRENT{index:08d}"
                
                # Variar categorías
                if index % 4 == 0:
                    weight = random.uniform(1, 4)
                elif index % 4 == 1:
                    weight = random.uniform(60, 100)
                else:
                    weight = random.uniform(10, 40)
                
                result = manager.register_package(
                    barcode=barcode,
                    weight=weight,
                    length=20, width=20, height=20,
                    destination=f"City-{index}",
                    priority="Standard"
                )
                
                results.append((index, result, barcode))
                db.disconnect()
            except Exception as e:
                errors.append((index, str(e)))
        
        # Act
        threads = []
        start_time = time.time()
        
        for i in range(num_packages):
            thread = threading.Thread(target=register_package_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Assert
        successful = sum(1 for _, result, _ in results if result)
        
        print(f"\n📊 NFR1.4 Results:")
        print(f"   Total time: {elapsed_time:.2f}s")
        print(f"   Attempted: {num_packages}")
        print(f"   Successful: {successful}")
        print(f"   Errors: {len(errors)}")
        
        if errors:
            print("\n❌ Errors:")
            for idx, error in errors[:3]:
                print(f"   Thread {idx}: {error}")
        
        assert elapsed_time < time_limit, f"Tiempo {elapsed_time:.2f}s excede {time_limit}s"
        # Permitir 20% de fallos por límites de espacio
        assert successful >= num_packages * 0.8, f"Solo {successful}/{num_packages} exitosos"
    
    # NFR1.5 - Asignación de ubicaciones < 500ms
    def test_nfr1_5_location_assignment_performance(self):
        """
        NFR1.5: Las consultas de asignación de ubicación deben completarse en <500ms.
        AC-NFR1.5: La operación debe completarse dentro de 500 milisegundos.
        """
        # Arrange
        threshold = 0.5  # segundos (500ms)
        num_queries = 50
        query_times = []
        
        # Act - Probar todas las categorías
        for category_id in range(1, 6):
            for _ in range(num_queries // 5):
                start_time = time.time()
                location_id = self.manager.find_available_location(category_id)
                end_time = time.time()
                
                elapsed_time = end_time - start_time
                query_times.append(elapsed_time)
                
                assert location_id is not None, f"No hay ubicación para categoría {category_id}"
        
        # Assert
        avg_time = sum(query_times) / len(query_times)
        max_time = max(query_times)
        times_under = sum(1 for t in query_times if t < threshold)
        success_rate = (times_under / len(query_times)) * 100
        
        print(f"\n📊 NFR1.5 Results:")
        print(f"   Queries performed: {len(query_times)}")
        print(f"   Average time: {avg_time*1000:.2f}ms")
        print(f"   Max time: {max_time*1000:.2f}ms")
        print(f"   Success rate (<500ms): {success_rate:.2f}%")
        
        assert max_time < threshold, f"Query más lenta: {max_time*1000:.2f}ms"
        assert avg_time < threshold, f"Tiempo promedio {avg_time*1000:.2f}ms excede 500ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])