#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

from uuid import uuid4
from esdl.processing import ESDLEcore
from esdl.processing.EcoreDocumentation import EcoreDocumentation
from extensions.session_manager import get_handler, get_session
from extensions.profiles import Profiles
import esdl.esdl
import src.log as log

logger = log.get_logger(__name__)


class ESDLDataLayer:
    def __init__(self, esdl_doc: EcoreDocumentation):
        self.esdl_doc = esdl_doc
        pass

    def get_object_info_by_identifier(self, identifier):
        esdl_object = self.get_object_from_identifier(identifier)
        return self.get_object_info(esdl_object)

    def get_standard_profiles_list(self):
        profiles = Profiles.get_instance().get_profiles()['profiles']
        profiles_list = list()
        for pkey in profiles:
            p = profiles[pkey]
            profiles_list.append({
                'id': pkey,
                'name': p['profile_uiname']
            })
        return profiles_list

    def get_datetime_profile(self):
        pass

    @staticmethod
    def get_area_object_list_of_type(type):
        active_es_id = get_session('active_es_id')
        esh = get_handler()
        
        es = esh.get_energy_system(active_es_id)
        area = es.instance[0].area
        object_list = list()
        for area_asset in area.eAllContents():
            if isinstance(area_asset, type):
                object_list.append({'id': area_asset.id, 'name': area_asset.name})
        return object_list       

    @staticmethod
    def remove_control_strategy(asset):
        active_es_id = get_session('active_es_id')
        esh = get_handler()

        cs = asset.controlStrategy
        if cs:
            services = cs.eContainer()
            services.service.remove(cs)
            esh.remove_object_from_dict(active_es_id, cs)
            asset.controlStrategy = None

    def get_services(self):
        active_es_id = get_session('active_es_id')
        esh = get_handler()

        es = esh.get_energy_system(active_es_id)
        services = es.services
        if not services:
            services = esdl.Services(id=str(uuid4()))
            es.services = services
        return services

    def get_table(self):
        pass

    def get_filtered_type(self, esdl_object, reference):
        """
        :param EObject esdl_object: the esdl class instance (e.g. 'esdl.WindTurbine')
        :param EReference reference: the reference to find the possible types for (e.g. 'controlStrategy')

        :return: list of possible types
        """
        types = []
        reference_type = reference.eType
        if isinstance(reference_type, esdl.ControlStrategy):
            if isinstance(esdl_object, esdl.Producer):
                types.append(esdl.CurtailmentStrategy.eClass.name)
            if isinstance(esdl_object, esdl.Storage):
                types.append(esdl.StorageStrategy.eClass.name)
            if isinstance(esdl_object, esdl.Conversion):
                types.append(esdl.DrivenByDemand.eClass.name)
                types.append(esdl.DrivenBySupply.eClass.name)
                types.append(esdl.DrivenByProfile.eClass.name)
        else:
            types = ESDLEcore.find_types(reference)
        return types

    def get_object_from_identifier(self, identifier):
        active_es_id = get_session('active_es_id')
        esh = get_handler()
        if 'id' in identifier:
            object_id = identifier['id']
            #object_id is not None:
            try:
                the_object = esh.get_by_id(active_es_id, object_id)
            except KeyError:
                logger.error('KeyError for getting id {} in uuid_dict. Trying fragment.'.format(object_id))
                resource = esh.get_resource(active_es_id)
                the_object = resource.resolve(identifier['fragment'])
        else:
            resource = esh.get_resource(active_es_id)
            the_object = resource.resolve(identifier['fragment'])

        return the_object

    def get_object_info(self, esdl_object):
        esdl_object_descr = self.get_object_dict(esdl_object)
        container = esdl_object.eContainer()
        container_descr = self.get_container_dict(container)
        attributes = ESDLEcore.get_asset_attributes(esdl_object, self.esdl_doc)
        references = ESDLEcore.get_asset_references(esdl_object, self.esdl_doc, ESDLDataLayer.generate_repr)
        return {
            'object': esdl_object_descr,
            'attributes': attributes,
            'references': references,
            'container': container_descr
        }
    
    def get_container_dict(self, container):
        if container is None:
            return None
        c_dict = {'doc': container.__doc__, 'type': container.eClass.name,}
        if hasattr(container, 'name'):
            c_dict['name']= container.name
        else:
            c_dict['name'] = None
        if not hasattr(container, 'id') or container.id is None:
            c_dict['fragment'] = container.eURIFragment()
        else:
            c_dict['id'] = container.id
        if container.eContainer() is not None:
            c_dict['container'] = self.get_container_dict(container.eContainer())
        return c_dict

    def get_object_dict(self, esdl_object):
        if not hasattr(esdl_object, 'name'):
            name = esdl_object.eClass.name
        else:
            name = esdl_object.name

        object_dict = {'name': name,
                        'doc': esdl_object.__doc__,
                        'type': esdl_object.eClass.name
                        }
        if not hasattr(esdl_object, 'id'):
            object_dict['id'] = None
            object_dict['fragment'] = esdl_object.eURIFragment()
        else:
            object_dict['id'] = esdl_object.id
        return object_dict

    @staticmethod
    def generate_repr(item):
        if item is None:
            return item
        if isinstance(item, esdl.Port):
            name = item.name
            if name is None:
                name = item.eClass.name
            return name + ' (' + item.eClass.name + ")"
        return item.eClass.name